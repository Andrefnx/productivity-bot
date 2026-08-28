require('dotenv').config();

const {
  ActionRowBuilder, ButtonBuilder, ButtonStyle, Client, EmbedBuilder, Events, GatewayIntentBits,
  ModalBuilder, REST, SlashCommandBuilder, StringSelectMenuBuilder, TextInputBuilder, TextInputStyle
} = require('discord.js');
const { readJson, writeJson } = require('./src/persistence');
const { awardSprintResult, getProfile } = require('./src/economy');
const { canCreateSprint, canManageSprintAction, defaultChannelConfig, defaultUserConfig, getChannelConfig, getUserConfig, updateChannelConfig, updateUserConfig } = require('./src/config');
const { createProject, getProjects, updateProject } = require('./src/projects');

if (!process.env.DISCORD_TOKEN) throw new Error('DISCORD_TOKEN was not found in the environment.');

const client = new Client({ intents: [GatewayIntentBits.Guilds] });
const activeSprints = new Map();
const commands = [
  new SlashCommandBuilder().setName('sprint').setDescription('Start a writing sprint'),
  new SlashCommandBuilder().setName('profile').setDescription('Open your profile'),
  new SlashCommandBuilder().setName('config').setDescription('Manage your settings'),
  new SlashCommandBuilder().setName('help').setDescription('Learn how to use the bot')
].map(command => command.toJSON());

const field = (label, value, inline = false) => ({ name: label, value: value || '\u200b', inline });
const ownerOnly = (interaction, ownerId) => String(interaction.user.id) === String(ownerId);
const button = (id, label, style = ButtonStyle.Secondary, disabled = false) => new ButtonBuilder().setCustomId(id).setLabel(label).setStyle(style).setDisabled(disabled);

function sprintComponents(sprint) {
  return [new ActionRowBuilder().addComponents(
    button(`sprint:join:${sprint.id}`, 'Join', ButtonStyle.Primary, sprint.finished),
    button(`sprint:leave:${sprint.id}`, 'Leave', ButtonStyle.Secondary, sprint.finished),
    button(`sprint:cancel:${sprint.id}`, 'Cancel Sprint', ButtonStyle.Danger, sprint.finished),
    button(`sprint:time:${sprint.id}`, 'Change Sprint Time', ButtonStyle.Secondary, sprint.finished),
    button(`sprint:settings:${sprint.id}`, 'Sprint Settings', ButtonStyle.Secondary, sprint.finished)
  ), new ActionRowBuilder().addComponents(button(`sprint:activity:${sprint.id}`, 'Edit Sprint Activity', ButtonStyle.Secondary, sprint.finished))];
}

function participantsText(sprint) { return sprint.participants.length ? sprint.participants.map(participant => `<@${participant.user_id}>`).join('\n') : 'No participants yet.'; }
function waitingEmbed(sprint, updated = false) { return new EmbedBuilder().setTitle('✍️ Productivity time!').setDescription(updated ? 'Sprint time updated!' : 'Get ready to focus!').addFields(field('Duration', `${sprint.duration} minutes`, true), field('Starts', `<t:${sprint.startTimestamp}:R>`, true), field('Participants', participantsText(sprint))); }
function startedEmbed(sprint) { return new EmbedBuilder().setTitle('Sprint started!').setDescription(`Time to focus!\nEnds <t:${sprint.endTimestamp}:R>.`).addFields(field('Duration', `${sprint.duration} minutes`, true), field('Participants', participantsText(sprint))); }
function finishedEmbed(sprint) { return new EmbedBuilder().setTitle('🏁 Sprint finished!').setDescription('Time is up!').addFields(field('Duration', `${sprint.duration} minutes`, true), field('Participants', participantsText(sprint)), field('Register your word count', `Registration closes <t:${sprint.resultDeadline}:R>.`)); }

async function saveActiveSprints() { await writeJson('active_sprints.json', [...activeSprints.values()].map(({ timers, ...sprint }) => sprint)); }
function schedule(sprint) {
  const now = Date.now();
  const delay = Math.max(0, (sprint.startTimestamp * 1000) - now);
  sprint.timers = { start: setTimeout(() => startSprint(sprint), delay), finish: null, results: null };
}
async function updateSprintMessage(sprint, embed, components = sprintComponents(sprint)) {
  const channel = await client.channels.fetch(sprint.channelId); const message = await channel.messages.fetch(sprint.messageId);
  await message.edit({ embeds: [embed], components });
}
async function startSprint(sprint) {
  if (sprint.finished || sprint.started) return;
  sprint.started = true; sprint.endTimestamp = Math.floor(Date.now() / 1000) + sprint.duration * 60;
  await updateSprintMessage(sprint, startedEmbed(sprint)); await saveActiveSprints();
  sprint.timers.finish = setTimeout(() => finishSprint(sprint), sprint.duration * 60 * 1000);
}
async function finishSprint(sprint) {
  if (sprint.finished) return;
  sprint.finished = true; sprint.resultDeadline = Math.floor(Date.now() / 1000) + 600;
  await updateSprintMessage(sprint, finishedEmbed(sprint), [new ActionRowBuilder().addComponents(button(`sprint:result:${sprint.id}`, 'Register Word Count', ButtonStyle.Primary))]);
  sprint.timers.results = setTimeout(() => closeResults(sprint), 600000); await saveActiveSprints();
}
async function closeResults(sprint) {
  for (const participant of sprint.participants) await awardSprintResult(participant, sprint.duration, sprint.id);
  const ranked = [...sprint.participants].filter(item => item.words_written !== null).sort((left, right) => right.words_written - left.words_written);
  const description = ranked.length ? ranked.map((item, index) => `${['🥇', '🥈', '🥉'][index] ?? `#${index + 1}`} **${item.display_name}**\n${item.words_written >= 0 ? `*+${item.words_written.toLocaleString()} words*` : `*${item.words_written.toLocaleString()} words*`}\nNew total for ***${item.project ?? 'No project'}*** is **${item.final_wc?.toLocaleString() ?? 'unknown'} words**`).join('\n\n') : 'No word counts were registered.';
  await updateSprintMessage(sprint, new EmbedBuilder().setTitle('🏆 Sprint Results').setDescription(description), []);
  activeSprints.delete(sprint.id); await saveActiveSprints();
}
async function recoverSprints() {
  const saved = await readJson('active_sprints.json', []);
  for (const item of saved) {
    try { const channel = await client.channels.fetch(item.channelId ?? item.channel_id); const message = await channel.messages.fetch(item.messageId ?? item.message_id); await message.edit({ embeds: [new EmbedBuilder().setTitle('🛠️ Bot out of order').setDescription('This sprint was interrupted because the bot went offline.\n\nSorry for the inconvenience.')], components: [] }); } catch (error) { console.error('Unable to mark interrupted sprint:', error.message); }
  }
  await writeJson('active_sprints.json', []);
}

function profileEmbed(user, profile) { const xp = Number(profile.xp ?? 0); return new EmbedBuilder().setTitle(`${user.displayName}'s Profile`).addFields(field('Level', `${profile.level ?? 1} ✦ ${xp % 100} / 100 XP`), field('Balance', `Total XP: ${xp}\nCoins: ${profile.economy?.coins ?? 0}`), field('Last Project', profile.last_project_id ?? 'None yet')); }
function profileComponents(userId) { return [new ActionRowBuilder().addComponents(button(`profile:projects:${userId}`, 'My Projects', ButtonStyle.Primary), button(`profile:settings:${userId}`, 'Settings'), button(`profile:import:${userId}`, 'Import JSON'))]; }
function configEmbed(config, title = 'Settings') { return new EmbedBuilder().setTitle(title).setDescription('Choose a setting to change.').addFields(...Object.entries(config).map(([key, value]) => field(key.replaceAll('_', ' '), String(value), true))); }
function configSelect(id, config) { return new ActionRowBuilder().addComponents(new StringSelectMenuBuilder().setCustomId(id).setPlaceholder('Select a setting').addOptions(Object.entries(config).map(([key, value]) => ({ label: key.replaceAll('_', ' ').slice(0, 100), value: key, description: String(value).slice(0, 100) })))); }

async function showProjects(interaction, userId) {
  const projects = await getProjects(userId); const entries = Object.entries(projects);
  const embed = new EmbedBuilder().setTitle('My Projects').setDescription(entries.length ? entries.map(([, project]) => `**${project.name}** - ${project.status}\n${project.wordcount ?? 0} words`).join('\n\n').slice(0, 4096) : 'No projects yet.');
  const components = [new ActionRowBuilder().addComponents(button(`project:create:${userId}`, 'Create Project', ButtonStyle.Primary), button(`profile:back:${userId}`, 'Back'))];
  if (entries.length) {
    const select = new StringSelectMenuBuilder()
      .setCustomId(`project:select:${userId}`)
      .setPlaceholder('Select a project')
      .addOptions(entries.slice(0, 25).map(([id, project]) => ({
        label: project.name.slice(0, 100),
        value: id,
        description: `${project.status} | ${project.wordcount ?? 0} words`.slice(0, 100)
      })));
    components.unshift(new ActionRowBuilder().addComponents(select));
  }
  await interaction.update({ embeds: [embed], components });
}

client.once(Events.ClientReady, async readyClient => {
  console.log(`Logged in as: ${readyClient.user.tag}`);
  try { await new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN).put(`/applications/${readyClient.user.id}/commands`, { body: commands }); console.log(`Synced commands: ${commands.length}`); } catch (error) { console.error('Command registration failed:', error); }
  await recoverSprints(); console.log('Bot ready for use');
});

client.on(Events.InteractionCreate, async interaction => {
  try {
    if (interaction.isChatInputCommand()) {
      if (interaction.commandName === 'sprint') { const config = await getChannelConfig(interaction.guildId, interaction.channelId); if (!canCreateSprint(interaction.member, config.create_sprints)) return interaction.reply({ content: 'You do not have permission to create sprints in this channel.', ephemeral: true }); const modal = new ModalBuilder().setCustomId('sprint:create').setTitle('Create a Sprint').addComponents(new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('duration').setLabel('Duration in minutes').setStyle(TextInputStyle.Short).setValue(String(config.default_duration)).setRequired(true)), new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('waiting').setLabel('Start waiting time in minutes').setStyle(TextInputStyle.Short).setValue(String(config.start_waiting_time)).setRequired(true))); return interaction.showModal(modal); }
      if (interaction.commandName === 'profile') { const profile = await getProfile(interaction.user.id); return interaction.reply({ embeds: [profileEmbed(interaction.user, profile)], components: profileComponents(interaction.user.id), ephemeral: true }); }
      if (interaction.commandName === 'config') { const config = await getUserConfig(interaction.user.id); return interaction.reply({ embeds: [configEmbed(config)], components: [configSelect(`config:user:${interaction.user.id}`, config), new ActionRowBuilder().addComponents(button(`config:channel:${interaction.user.id}`, 'Channel Settings'))], ephemeral: true }); }
      if (interaction.commandName === 'help') { const sections = { 'Getting Started': '**Main commands**\n\n`/sprint` - Start a new productivity sprint.\n`/profile` - Open your personal profile menu.\n`/config` - Change your privacy and display settings.\n`/help` - Open this guide.', Sprints: 'Use `/sprint` and choose how long the sprint should last and when it should begin. Press **Join** and choose a project. At the end, register your final word count.', Projects: 'Use `/profile` and press **My Projects** to create, edit and select projects.', Profile: 'Your profile shows your XP, level, coins and last project.', Settings: 'Use `/config` to change privacy, date and time settings.', Imports: 'Open `/profile`, press **Import JSON**, then upload a Writer Bot export.' }; return interaction.reply({ embeds: [new EmbedBuilder().setTitle('Help').setDescription('Welcome! This guide explains how to use the bot.')], components: [new ActionRowBuilder().addComponents(new StringSelectMenuBuilder().setCustomId(`help:${interaction.user.id}`).setPlaceholder('Choose a section').addOptions(Object.keys(sections).map(key => ({ label: key, value: key }))))], ephemeral: true }); }
    }
    if (interaction.isModalSubmit()) {
      if (interaction.customId === 'sprint:create') { const duration = Number(interaction.fields.getTextInputValue('duration')); const waiting = Number(interaction.fields.getTextInputValue('waiting')); if (!Number.isInteger(duration) || !Number.isInteger(waiting) || duration <= 0 || waiting < 0) return interaction.reply({ content: 'Duration must be greater than 0, and start time cannot be negative.', ephemeral: true }); const id = `${interaction.guildId}-${interaction.channelId}-${Date.now()}`; const sprint = { id, guildId: interaction.guildId, channelId: interaction.channelId, creatorId: interaction.user.id, duration, startTimestamp: Math.floor(Date.now() / 1000) + waiting * 60, participants: [], started: false, finished: false }; await interaction.reply({ embeds: [waitingEmbed(sprint)], components: sprintComponents(sprint) }); const reply = await interaction.fetchReply(); sprint.messageId = reply.id; activeSprints.set(id, sprint); schedule(sprint); return saveActiveSprints(); }
      if (interaction.customId.startsWith('sprint:time:')) { const sprintId = interaction.customId.split(':')[2]; const sprint = activeSprints.get(sprintId); if (!sprint || sprint.started) return interaction.reply({ content: 'This sprint has already started or is no longer active.', ephemeral: true }); const duration = Number(interaction.fields.getTextInputValue('duration')); const waiting = Number(interaction.fields.getTextInputValue('waiting')); if (!Number.isInteger(duration) || !Number.isInteger(waiting) || duration <= 0 || waiting < 0) return interaction.reply({ content: 'Duration must be greater than 0, and start time cannot be negative.', ephemeral: true }); clearTimeout(sprint.timers.start); sprint.duration = duration; sprint.startTimestamp = Math.floor(Date.now() / 1000) + waiting * 60; schedule(sprint); await updateSprintMessage(sprint, waitingEmbed(sprint, true)); await saveActiveSprints(); return interaction.reply({ content: 'Sprint time updated!', ephemeral: true }); }
      if (interaction.customId.startsWith('project:create:')) { const userId = interaction.customId.split(':')[2]; const project = await createProject(userId, { name: interaction.fields.getTextInputValue('name'), description: interaction.fields.getTextInputValue('description'), wordcount: interaction.fields.getTextInputValue('wordcount'), goal: interaction.fields.getTextInputValue('goal'), status: 'Active' }); return interaction.reply({ content: `Project **${project.name}** created.`, ephemeral: true }); }
      if (interaction.customId.startsWith('result:')) { const [, sprintId] = interaction.customId.split(':'); const sprint = activeSprints.get(sprintId); if (!sprint) return interaction.reply({ content: 'This sprint is no longer active.', ephemeral: true }); const participant = sprint.participants.find(item => item.user_id === interaction.user.id); const total = interaction.fields.getTextInputValue('total').trim(); const difference = interaction.fields.getTextInputValue('difference').trim(); if (!!total === !!difference) return interaction.reply({ content: total ? "Pick only one option. Don't enter both your new total and your word count change." : 'Pick one option:\n• New total word count\n• Words added or removed', ephemeral: true }); if (total && (!/^\d+$/.test(total) || Number(total) < 0)) return interaction.reply({ content: 'New total must be a non-negative number.', ephemeral: true }); if (difference && !/^[+-]\d+$/.test(difference)) return interaction.reply({ content: 'Word count change must be a number like +234 or -120.', ephemeral: true }); participant.final_wc = total ? Number(total) : participant.initial_wc + Number(difference); if (participant.final_wc < 0) return interaction.reply({ content: 'That change would make your total word count negative.', ephemeral: true }); participant.words_written = participant.final_wc - participant.initial_wc; await saveActiveSprints(); return interaction.reply({ content: 'Word count registered.', ephemeral: true }); }
    }
    if (interaction.isButton()) {
      const [area, action, id] = interaction.customId.split(':');
      if (area === 'profile') { if (!ownerOnly(interaction, id)) return interaction.reply({ content: 'This menu belongs to another user.', ephemeral: true }); if (action === 'projects') return showProjects(interaction, id); if (action === 'settings') return interaction.update({ embeds: [configEmbed(await getUserConfig(id))], components: [configSelect(`config:user:${id}`, await getUserConfig(id))] }); if (action === 'import') return interaction.reply({ content: 'Import JSON is available for Writer Bot exports. Attachment imports are not yet supported by this Node runtime.', ephemeral: true }); if (action === 'back') return interaction.update({ embeds: [profileEmbed(interaction.user, await getProfile(id))], components: profileComponents(id) }); }
      if (area === 'project' && action === 'create') { if (!ownerOnly(interaction, id)) return interaction.reply({ content: 'This menu belongs to another user.', ephemeral: true }); const modal = new ModalBuilder().setCustomId(`project:create:${id}`).setTitle('Create Project').addComponents(...[['name', 'Project name', true], ['description', 'Description', false], ['wordcount', 'Current word count', true], ['goal', 'Word count goal', false]].map(([key, label, required]) => new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId(key).setLabel(label).setStyle(TextInputStyle.Short).setRequired(required)))); return interaction.showModal(modal); }
      if (area === 'config' && action === 'channel') { if (!ownerOnly(interaction, id) || !interaction.member.permissions.has('ManageGuild')) return interaction.reply({ content: 'Only administrators or server managers can edit channel settings.', ephemeral: true }); const config = await getChannelConfig(interaction.guildId, interaction.channelId); return interaction.update({ embeds: [configEmbed(config, 'Channel Settings')], components: [configSelect(`config:channel:${id}`, config)] }); }
      if (area === 'sprint') { const sprint = activeSprints.get(id); if (!sprint) return interaction.reply({ content: 'This sprint is no longer active.', ephemeral: true }); if (action === 'join') { if (sprint.participants.some(item => item.user_id === interaction.user.id)) return interaction.reply({ content: 'You are already in this sprint.', ephemeral: true }); const projects = await getProjects(interaction.user.id); const options = Object.entries(projects).slice(0, 25).map(([projectId, project]) => ({ label: project.name.slice(0, 100), value: projectId, description: `${project.wordcount ?? 0} words` })); if (!options.length) return interaction.reply({ content: 'You need to create a project in `/profile` before joining.', ephemeral: true }); return interaction.reply({ content: 'How do you want to join?', components: [new ActionRowBuilder().addComponents(new StringSelectMenuBuilder().setCustomId(`sprint:project:${id}`).setPlaceholder('Select a project').addOptions(options))], ephemeral: true }); }
        if (action === 'leave') { const config = await getChannelConfig(sprint.guildId, sprint.channelId); if (sprint.started && !config.allow_leave_after_start) return interaction.reply({ content: 'You cannot leave after this sprint has started.', ephemeral: true }); sprint.participants = sprint.participants.filter(item => item.user_id !== interaction.user.id); await updateSprintMessage(sprint, sprint.started ? startedEmbed(sprint) : waitingEmbed(sprint)); await saveActiveSprints(); return interaction.reply({ content: 'You left the sprint!', ephemeral: true }); }
        if (action === 'cancel' || action === 'time') { const config = await getChannelConfig(sprint.guildId, sprint.channelId); const setting = action === 'cancel' ? config.cancel_sprints : config.change_sprint_time; if (!canManageSprintAction(interaction.member, sprint.creatorId, setting)) return interaction.reply({ content: 'You do not have permission to manage this sprint.', ephemeral: true }); if (action === 'cancel') { sprint.finished = true; clearTimeout(sprint.timers.start); clearTimeout(sprint.timers.finish); await updateSprintMessage(sprint, new EmbedBuilder().setTitle('Sprint cancelled').setDescription(`The sprint was cancelled by **${interaction.user.username}**.`), []); activeSprints.delete(id); await saveActiveSprints(); return interaction.reply({ content: 'Sprint cancelled.', ephemeral: true }); } const modal = new ModalBuilder().setCustomId(`sprint:time:${id}`).setTitle('Change Sprint Time').addComponents(new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('duration').setLabel('Duration in minutes').setStyle(TextInputStyle.Short).setValue(String(sprint.duration))), new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('waiting').setLabel('Start waiting time in minutes').setStyle(TextInputStyle.Short).setValue('0'))); return interaction.showModal(modal); }
        if (action === 'activity') return interaction.reply({ content: 'Edit Sprint Activity is available by registering progress when the sprint ends.', ephemeral: true });
        if (action === 'result') { const participant = sprint.participants.find(item => item.user_id === interaction.user.id); if (!participant) return interaction.reply({ content: 'You were not in the sprint when it finished.', ephemeral: true }); if (participant.words_written !== null) return interaction.reply({ content: 'You already registered your word count.', ephemeral: true }); const modal = new ModalBuilder().setCustomId(`result:${id}`).setTitle('Register Word Count').addComponents(new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('total').setLabel('New total word count').setStyle(TextInputStyle.Short).setRequired(false)), new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('difference').setLabel('Words added or removed, e.g. +234').setStyle(TextInputStyle.Short).setRequired(false))); return interaction.showModal(modal); }
      }
    }
    if (interaction.isStringSelectMenu()) {
      const [area, action, id] = interaction.customId.split(':'); const value = interaction.values[0];
      if (area === 'help') { if (!ownerOnly(interaction, action)) return interaction.reply({ content: 'This help menu belongs to another user.', ephemeral: true }); const copy = { 'Getting Started': 'Use `/sprint`, `/profile`, `/config`, and `/help`.', Sprints: 'Create a sprint, join with a project, then register your final word count.', Projects: 'Create and select projects from your profile.', Profile: 'View XP, level, coins and your last project.', Settings: 'Set privacy, time format and timezone.', Imports: 'Writer Bot JSON imports are documented here.' }; return interaction.update({ embeds: [new EmbedBuilder().setTitle(value).setDescription(copy[value])], components: interaction.message.components }); }
      if (area === 'config') { if (!ownerOnly(interaction, id)) return interaction.reply({ content: 'This settings menu belongs to another user.', ephemeral: true }); const isChannel = action === 'channel'; const config = isChannel ? await getChannelConfig(interaction.guildId, interaction.channelId) : await getUserConfig(id); const current = config[value]; const options = typeof current === 'boolean' ? [{ label: 'Allowed', value: 'true' }, { label: 'Disabled', value: 'false' }] : value.includes('sprints') || value.includes('sprint_time') ? [{ label: 'Everyone', value: 'everyone' }, { label: 'Creator or moderator', value: 'creator_or_moderator' }, { label: 'Administrators', value: 'admin' }] : value.includes('visibility') ? [{ label: 'Public', value: 'public' }, { label: 'Private', value: 'private' }] : value === 'time_format' ? [{ label: '12-hour', value: '12h' }, { label: '24-hour', value: '24h' }] : [{ label: String(current), value: String(current) }]; return interaction.update({ embeds: [new EmbedBuilder().setTitle('Settings').setDescription(`Choose a value for ${value.replaceAll('_', ' ')}.`)], components: [new ActionRowBuilder().addComponents(new StringSelectMenuBuilder().setCustomId(`configvalue:${action}:${id}:${value}`).setPlaceholder('Select a value').addOptions(options))] }); }
      if (area === 'configvalue') { const [, type, userId, key] = interaction.customId.split(':'); let parsed = value === 'true' ? true : value === 'false' ? false : value; if (type === 'channel') await updateChannelConfig(interaction.guildId, interaction.channelId, key, parsed); else await updateUserConfig(userId, key, parsed); return interaction.update({ embeds: [new EmbedBuilder().setTitle('Settings').setDescription('Setting saved.')], components: [] }); }
      if (area === 'project' && action === 'select') { if (!ownerOnly(interaction, id)) return interaction.reply({ content: 'This menu belongs to another user.', ephemeral: true }); const project = (await getProjects(id))[value]; return interaction.update({ embeds: [new EmbedBuilder().setTitle(project.name).setDescription(project.description || 'No description.').addFields(field('Status', project.status, true), field('Word count', String(project.wordcount ?? 0), true), field('Goal', String(project.goal ?? 'None'), true))], components: [new ActionRowBuilder().addComponents(button(`profile:projects:${id}`, 'Back'))] }); }
      if (area === 'sprint' && action === 'project') { const sprint = activeSprints.get(id); if (!sprint) return interaction.reply({ content: 'This sprint is no longer active.', ephemeral: true }); const project = (await getProjects(interaction.user.id))[value]; sprint.participants.push({ user_id: interaction.user.id, display_name: interaction.user.displayName, project_id: value, project: project.name, initial_wc: Number(project.wordcount ?? 0), final_wc: null, words_written: null }); await updateSprintMessage(sprint, sprint.started ? startedEmbed(sprint) : waitingEmbed(sprint)); await saveActiveSprints(); return interaction.update({ content: 'You joined the sprint!', components: [] }); }
    }
  } catch (error) { console.error('Interaction failed:', error); if (interaction.isRepliable()) { const payload = { content: 'Something went wrong while processing that action. Please try again.', ephemeral: true }; if (interaction.deferred || interaction.replied) await interaction.followUp(payload).catch(() => {}); else await interaction.reply(payload).catch(() => {}); } }
});

client.login(process.env.DISCORD_TOKEN);