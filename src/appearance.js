const allowedImageTypes = new Set(['image/png', 'image/jpeg', 'image/webp', 'image/gif']);
const allowedCdnHosts = new Set(['cdn.discordapp.com', 'media.discordapp.net']);
const maximumAvatarBytes = 10 * 1024 * 1024;

function isBotOwner(userId, ownerId = process.env.BOT_OWNER_ID) {
  return Boolean(ownerId) && String(userId) === String(ownerId);
}

function validateNickname(value) {
  const nickname = value.trim();
  if (!nickname) return { valid: false, error: 'Bot name cannot be empty.' };
  if (nickname.length > 32) return { valid: false, error: 'Bot name must be 32 characters or fewer.' };
  return { valid: true, nickname };
}

function validateAvatarUrl(value) {
  let url;
  try {
    url = new URL(value.trim());
  } catch {
    return { valid: false, error: 'Provide a valid Discord CDN image URL.' };
  }

  if (url.protocol !== 'https:' || !allowedCdnHosts.has(url.hostname)) {
    return { valid: false, error: 'Avatar images must use an HTTPS URL from the Discord CDN.' };
  }

  return { valid: true, url };
}

async function downloadAvatar(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);

  try {
    const response = await fetch(url, { signal: controller.signal });
    const contentType = response.headers.get('content-type')?.split(';')[0].toLowerCase();
    const contentLength = Number(response.headers.get('content-length') ?? 0);
    if (!response.ok) throw new Error(`The image download failed with HTTP ${response.status}.`);
    if (!allowedImageTypes.has(contentType)) throw new Error('The avatar must be a PNG, JPEG, WEBP, or GIF image.');
    if (contentLength > maximumAvatarBytes) throw new Error('The avatar image is too large. Maximum size is 10 MiB.');
    const bytes = Buffer.from(await response.arrayBuffer());
    if (bytes.length > maximumAvatarBytes) throw new Error('The avatar image is too large. Maximum size is 10 MiB.');
    return bytes;
  } finally {
    clearTimeout(timeout);
  }
}

module.exports = { downloadAvatar, isBotOwner, maximumAvatarBytes, validateAvatarUrl, validateNickname };