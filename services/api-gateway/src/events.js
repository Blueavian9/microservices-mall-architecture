const { connect, StringCodec } = require('nats');
const { v4: uuidv4 } = require('uuid');

let nc = null;

const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000];

/**
 * Connect to NATS with exponential backoff (5 retries after initial attempt).
 * Does not throw — logs warnings if NATS stays unavailable.
 */
async function connectNATS() {
  const url = process.env.NATS_URL;
  if (!url) {
    console.warn('NATS_URL not set; NATS disabled');
    return;
  }

  let lastErr;
  for (let attempt = 0; attempt <= BACKOFF_MS.length; attempt += 1) {
    try {
      nc = await connect({ servers: url });
      console.info('NATS connected');
      return;
    } catch (err) {
      lastErr = err;
      console.warn(`NATS connect attempt ${attempt + 1} failed:`, err.message);
      if (attempt < BACKOFF_MS.length) {
        await new Promise((resolve) => setTimeout(resolve, BACKOFF_MS[attempt]));
      }
    }
  }
  console.warn('NATS unavailable after retries; continuing without NATS:', lastErr?.message);
}

/**
 * Publish event with contract shape. No-op if NATS is down (service keeps running).
 */
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
