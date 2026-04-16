const { connect, StringCodec } = require('nats');

const NATS_URL    = process.env.NATS_URL || 'nats://nats:4222';
const BUFFER_SIZE = 50;
const sc          = StringCodec();
let eventBuffer   = [];
let nc            = null;

async function subscribeAll() {
  let delay = 1000;
  while (true) {
    try {
      nc = await connect({ servers: NATS_URL });
      console.log(`[nats] Connected to ${NATS_URL}`);
      delay = 1000;

      const sub = nc.subscribe('>');
      (async () => {
        for await (const msg of sub) {
          let data = {};
          try { data = JSON.parse(sc.decode(msg.data)); } catch {}
          const event = {
            event_id:  `${Date.now()}-${Math.random().toString(36).slice(2,7)}`,
            subject:   msg.subject,
            service:   msg.subject.split('.')[0],
            timestamp: new Date().toISOString(),
            data
          };
          eventBuffer.push(event);
          if (eventBuffer.length > BUFFER_SIZE) eventBuffer.shift();
        }
      })();

      await nc.closed();
      throw new Error('NATS connection closed');
    } catch (err) {
      console.error(`[nats] ${err.message}. Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
      delay = Math.min(delay * 2, 30000);
    }
  }
}

function getEvents() { return [...eventBuffer]; }

module.exports = { subscribeAll, getEvents };
