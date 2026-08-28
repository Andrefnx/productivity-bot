const { readJson, writeJson } = require('./persistence');

const defaultChannelConfig = {
  create_sprints: 'everyone', cancel_sprints: 'creator_or_moderator', change_sprint_time: 'creator_or_moderator',
  allow_join_after_start: true, allow_leave_after_start: true, allow_change_duration_after_start: false,
  allow_change_waiting_time: true, default_duration: 30, min_duration: 1, max_duration: 180,
  start_waiting_time: 10, word_count_waiting_time: 10, cancel_empty_sprints: true, empty_sprint_timeout: 10
};
const defaultUserConfig = { profile_visibility: 'private', projects_visibility: 'private', time_format: '12h', timezone: 'America/Punta_Arenas' };
const legacyKeys = { default_waiting_time: 'start_waiting_time', default_start_waiting_time: 'start_waiting_time' };

async function getChannelConfig(guildId, channelId) {
  const configs = await readJson('channel_config.json', {});
  const saved = configs[String(guildId)]?.[String(channelId)] ?? {};
  const mapped = Object.fromEntries(Object.entries(saved).flatMap(([key, value]) => legacyKeys[key] === undefined && key in legacyKeys ? [] : [[legacyKeys[key] ?? key, value]]));
  return { ...defaultChannelConfig, ...mapped };
}

async function updateChannelConfig(guildId, channelId, key, value) {
  if (!(key in defaultChannelConfig)) throw new Error(`Unknown channel config key: ${key}`);
  const configs = await readJson('channel_config.json', {});
  const guildKey = String(guildId); const channelKey = String(channelId);
  configs[guildKey] ??= {}; configs[guildKey][channelKey] ??= {};
  configs[guildKey][channelKey][key] = value;
  await writeJson('channel_config.json', configs);
}

async function getUserConfig(userId) {
  const { getProfile } = require('./economy');
  return { ...defaultUserConfig, ...((await getProfile(userId)).config ?? {}) };
}

async function updateUserConfig(userId, key, value) {
  if (!(key in defaultUserConfig)) throw new Error(`Unknown user config key: ${key}`);
  const { getProfile, updateProfile } = require('./economy');
  const profile = await getProfile(userId); const config = { ...defaultUserConfig, ...(profile.config ?? {}), [key]: value };
  await updateProfile(userId, { config }); return config;
}

function isModerator(member) { return member.permissions.has('Administrator') || member.permissions.has('ManageGuild') || member.permissions.has('ManageMessages'); }
function canCreateSprint(member, setting) { return setting === 'everyone' || setting === 'admin' && member.permissions.has('Administrator') || setting === 'manage_messages' && member.permissions.has('ManageMessages'); }
function canManageSprintAction(member, creatorId, setting) { return String(member.id) === String(creatorId) || setting === 'admin' && member.permissions.has('Administrator') || setting === 'creator_or_moderator' && isModerator(member); }

module.exports = { canCreateSprint, canManageSprintAction, defaultChannelConfig, defaultUserConfig, getChannelConfig, getUserConfig, isModerator, updateChannelConfig, updateUserConfig };