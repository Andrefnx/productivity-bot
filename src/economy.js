const { readJson, writeJson } = require('./persistence');

const defaultEconomy = {
  coins: 0,
  lifetime_xp: 0,
  lifetime_coins: 0,
  sprints_rewarded: 0,
  transactions: [],
  migrations: {},
  sprint_rewards: {}
};

const defaultProfile = {
  xp: 0,
  level: 1,
  last_project_id: null,
  imports: {},
  economy: defaultEconomy
};

function calculateLevel(xp) {
  return Math.floor(Math.max(0, Number(xp)) / 100) + 1;
}

async function getProfile(userId) {
  const profiles = await readJson('profiles.json', {});
  const profileKey = String(userId);
  const current = profiles[profileKey] ?? {};
  const profile = {
    ...structuredClone(defaultProfile),
    ...current,
    economy: { ...structuredClone(defaultEconomy), ...(current.economy ?? {}) }
  };

  if (JSON.stringify(current) !== JSON.stringify(profile)) {
    profiles[profileKey] = profile;
    await writeJson('profiles.json', profiles);
  }

  return profile;
}

async function updateProfile(userId, changes) {
  const profiles = await readJson('profiles.json', {});
  const profileKey = String(userId);
  profiles[profileKey] = { ...structuredClone(defaultProfile), ...(profiles[profileKey] ?? {}), ...changes };
  await writeJson('profiles.json', profiles);
  return profiles[profileKey];
}

function calculateSprintRewards(duration, wordsWritten) {
  if (wordsWritten === null || wordsWritten === undefined) {
    return { xp: 10, coins: 0 };
  }

  const safeDuration = Math.max(0, Number(duration));
  const positiveWords = Math.max(0, Number(wordsWritten));
  const durationXp = safeDuration < 15 ? 0 : safeDuration < 30 ? 2 : safeDuration < 60 ? 5 : safeDuration < 120 ? 10 : 15;
  return {
    xp: 15 + durationXp + Math.floor(positiveWords / 50),
    coins: Math.max(1, Math.floor(positiveWords / 100))
  };
}

async function awardSprintResult(sprintUser, duration, sprintId) {
  const profile = await getProfile(sprintUser.user_id);
  const rewardKey = `${sprintId}:${sprintUser.user_id}`;
  const economy = structuredClone(profile.economy);

  if (economy.sprint_rewards[rewardKey]) {
    return false;
  }

  const { xp, coins } = calculateSprintRewards(duration, sprintUser.words_written);
  const newXp = Number(profile.xp ?? 0) + xp;
  economy.coins = Number(economy.coins ?? 0) + coins;
  economy.lifetime_xp = Number(economy.lifetime_xp ?? 0) + xp;
  economy.lifetime_coins = Number(economy.lifetime_coins ?? 0) + coins;
  economy.sprints_rewarded = Number(economy.sprints_rewarded ?? 0) + 1;
  economy.sprint_rewards[rewardKey] = { xp, coins, sprint_id: sprintId, timestamp: Date.now() / 1000 };

  await updateProfile(sprintUser.user_id, { xp: newXp, level: calculateLevel(newXp), economy });
  return true;
}

module.exports = { awardSprintResult, calculateLevel, calculateSprintRewards, getProfile, updateProfile };