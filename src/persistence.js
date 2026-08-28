const fs = require('node:fs/promises');
const path = require('node:path');

const dataDirectory = path.join(__dirname, '..', 'data');
const writeQueues = new Map();

async function readJson(filename, fallback) {
  const filePath = path.join(dataDirectory, filename);

  try {
    return JSON.parse(await fs.readFile(filePath, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') {
      return structuredClone(fallback);
    }

    if (error instanceof SyntaxError) {
      console.error(`Invalid JSON in ${filePath}; using defaults.`, error);
      return structuredClone(fallback);
    }

    throw error;
  }
}

function writeJson(filename, data) {
  const previousWrite = writeQueues.get(filename) ?? Promise.resolve();
  const nextWrite = previousWrite.then(async () => {
    await fs.mkdir(dataDirectory, { recursive: true });
    const filePath = path.join(dataDirectory, filename);
    const temporaryPath = `${filePath}.${process.pid}.tmp`;
    await fs.writeFile(temporaryPath, `${JSON.stringify(data, null, 4)}\n`, 'utf8');
    await fs.rename(temporaryPath, filePath);
  });

  writeQueues.set(filename, nextWrite.catch(() => {}));
  return nextWrite;
}

module.exports = { readJson, writeJson };