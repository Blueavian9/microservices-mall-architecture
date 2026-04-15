const express = require('express');
const { WebSocketServer } = require('ws');
const http = require('http');
const { connect, StringCodec } = require('nats');
const client = require('prom-client');

const PORT = process.env.PORT || 3002;
const NATS_URL = process.env.NATS_URL || 'nats://nats:4222';

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

// Prometheus default metrics
client.collectDefaultMetrics();

// In-memory event log (last 100)
const eventLog = [];
const MAX_EVENTS = 100;

function broadcast(data) {
  const msg = JSON.stringify(data);
  wss.clients.forEach(ws => {
    if (ws.readyState === ws.OPEN) ws.send(msg);
  });
}

// NATS subscriber — forward all events to WebSocket clients
async function startNatsSubscriber() {
  try {
    const nc = await connect({ servers: NATS_URL });
    const sc = StringCodec();
    console.log(`[metrics-service] NATS connected: ${NATS_URL}`);

    const sub = nc.subscribe('>'); // wildcard — all subjects
    (async () => {
      for await (const msg of sub) {
        const event = {
          type: 'event',
          subject: msg.subject,
          data: sc.decode(msg.data),
          ts: new Date().toISOString(),
        };
        eventLog.push(event);
        if (eventLog.length > MAX_EVENTS) eventLog.shift();
        broadcast(event);
      }
    })();
  } catch (err) {
    console.warn(`[metrics-service] NATS unavailable (will retry on next restart): ${err.message}`);
  }
}

// WebSocket: send last 100 events on connect
wss.on('connection', (ws) => {
  console.log('[metrics-service] WebSocket client connected');
  ws.send(JSON.stringify({ type: 'history', events: eventLog }));
});

// HTTP routes
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'metrics-service' }));

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});

app.get('/events', (req, res) => res.json({ events: eventLog }));

server.listen(PORT, () => {
  console.log(`[metrics-service] HTTP+WS listening on :${PORT}`);
  startNatsSubscriber();
});
