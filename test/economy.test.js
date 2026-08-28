const test = require('node:test');
const assert = require('node:assert/strict');
const { calculateLevel, calculateSprintRewards } = require('../src/economy');

test('level formula matches Python', () => {
  assert.equal(calculateLevel(0), 1);
  assert.equal(calculateLevel(-1), 1);
  assert.equal(calculateLevel(99), 1);
  assert.equal(calculateLevel(100), 2);
  assert.equal(calculateLevel(333), 4);
});

test('sprint rewards match Python formulas', () => {
  assert.deepEqual(calculateSprintRewards(30, 250), { xp: 25, coins: 2 });
  assert.deepEqual(calculateSprintRewards(30, 0), { xp: 20, coins: 1 });
  assert.deepEqual(calculateSprintRewards(30, -50), { xp: 20, coins: 1 });
  assert.deepEqual(calculateSprintRewards(30, null), { xp: 10, coins: 0 });
});