const { connect, StringCodec } = require('nats');

let nc;
const sc = StringCodec();

async function connectNATS() {
  const url = process.env.NATS_URL || 'nats://localhost:4222';
  nc = await connect({ servers: url });
  console.info(`booking-service connected to NATS at ${url}`);
}

async function publishEvent(subject, data) {
  if (!nc) return;
  nc.publish(subject, sc.encode(JSON.stringify(data)));
}

async function drainNATS() {
  if (nc) await nc.drain();
}

module.exports = { connectNATS, publishEvent, drainNATS };
