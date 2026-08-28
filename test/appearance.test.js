const test = require('node:test');
const assert = require('node:assert/strict');
const { isBotOwner, validateAvatarUrl, validateNickname } = require('../src/appearance');

test('global appearance is owner-only and hides without owner configuration', () => {
  assert.equal(isBotOwner('42', ''), false);
  assert.equal(isBotOwner('42', '24'), false);
  assert.equal(isBotOwner('42', '42'), true);
});

test('nickname validation trims input and enforces Discord limit', () => {
  assert.deepEqual(validateNickname('  Focus Bot  '), { valid: true, nickname: 'Focus Bot' });
  assert.equal(validateNickname('   ').valid, false);
  assert.equal(validateNickname('a'.repeat(33)).valid, false);
});

test('avatar sources require HTTPS Discord CDN URLs', () => {
  assert.equal(validateAvatarUrl('https://cdn.discordapp.com/attachments/1/2/avatar.png').valid, true);
  assert.equal(validateAvatarUrl('http://cdn.discordapp.com/attachments/1/2/avatar.png').valid, false);
  assert.equal(validateAvatarUrl('https://example.com/avatar.png').valid, false);
  assert.equal(validateAvatarUrl('not a url').valid, false);
});