const { connect, StringCodec } = require('nats');
const { v4: uuidv4 } = require('uuid');

let nc = null;

/**
 * Exponential backoff after each failed connect: 1s, 2s, 4s, 8s, 16s.
 * Exactly `BACKOFF_MS.length` waits and `BACKOFF_MS.length + 1` attempts (initial try + retries).
 * Loop bound is `< maxAttempts`, never `<= BACKOFF_MS.length` (avoids an extra stray attempt).
 */
const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000];

/**
 * Connect to NATS with exponential backoff. Does not throw — logs and continues.
 */
async function connectNATS() {
  const url = process.env.NATS_URL;
  if (!url) {
    console.warn('NATS_URL not set; NATS disabled');
    return;
  }

  const maxAttempts = BACKOFF_MS.length + 1;
  let lastErr;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    try {
      nc = await connect({ servers: url });
      console.info('NATS connected');
      return;
    } catch (err) {
      lastErr = err;
      console.warn(
        `NATS connect attempt ${attempt + 1}/${maxAttempts} failed:`,
        err.message,
      );
      if (attempt < BACKOFF_MS.length) {
        await new Promise((resolve) => setTimeout(resolve, BACKOFF_MS[attempt]));
      }
    }
  }
  console.warn('NATS unavailable after retries; continuing without NATS:', lastErr?.message);
}

function publishEvent(subject, data) {
  if (!nc) {
    console.warn('publishEvent skipped (no NATS):', subject);
    return;
  }
  const sc = StringCodec();
  const payload = {
    event_id: uuidv4(),
    subject,
    service: 'api-gateway',
    timestamp: new Date().toISOString(),
    data,
  };
  try {
    nc.publish(subject, sc.encode(JSON.stringify(payload)));
  } catch (err) {
    console.warn('publishEvent failed:', err.message);
  }
}

async function drainNATS() {
  if (!nc) return;
  try {
    await nc.drain();
  } catch (err) {
    console.warn('NATS drain:', err.message);
  }
  nc = null;
}

module.exports = { connectNATS, publishEvent, drainNATS };
