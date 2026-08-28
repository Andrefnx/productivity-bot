const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { readJson, writeJson } = require('../src/persistence');
const { getProfile } = require('../src/economy');
const { defaultChannelConfig, defaultUserConfig } = require('../src/config');

test('JSON persistence reads defaults and writes atomically', async () => {
  const filename = `node-test-${process.pid}.json`;
  assert.deepEqual(await readJson(filename, { value: 0 }), { value: 0 });
  await Promise.all([writeJson(filename, { value: 1 }), writeJson(filename, { value: 2 })]);
  assert.deepEqual(await readJson(filename, {}), { value: 2 });
  await fs.unlink(path.join(__dirname, '..', 'data', filename));
});

test('profile and configuration defaults retain Python-compatible keys', async () => {
  const userId = `node-test-${process.pid}`;
  const profile = await getProfile(userId);
  assert.deepEqual(Object.keys(profile.economy).sort(), ['coins', 'lifetime_coins', 'lifetime_xp', 'migrations', 'sprint_rewards', 'sprints_rewarded', 'transactions']);
  assert.equal(profile.level, 1);
  assert.equal(defaultChannelConfig.default_duration, 30);
  assert.equal(defaultUserConfig.timezone, 'America/Punta_Arenas');
  const profiles = await readJson('profiles.json', {});
  delete profiles[userId];
  await writeJson('profiles.json', profiles);
});