const express    = require('express');
const { WebSocketServer } = require('ws');
const fetch      = require('node-fetch');
const { getPods }        = require('./k8s');
const { subscribeAll, getEvents } = require('./nats');

const PORT      = process.env.PORT || 4000;
const PROM_URL  = process.env.PROMETHEUS_URL || 'http://prometheus:9090';

const app = express();
app.get('/health', (_req, res) => res.json({ status: 'ok', service: 'metrics-service' }));
const server = app.listen(PORT, () => console.log(`[metrics] HTTP on :${PORT}`));

const wss = new WebSocketServer({ server });
wss.on('connection', ws => {
  console.log('[ws] client connected');
  ws.on('close', () => console.log('[ws] client disconnected'));
});

function broadcast(data) {
  const payload = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === 1) client.send(payload);
  });
}

async function fetchTraffic() {
  try {
    const url = `${PROM_URL}/api/v1/query?query=http_requests_total`;
    const res  = await fetch(url, { timeout: 3000 });
    const json = await res.json();
    const traffic = {};
    (json?.data?.result || []).forEach(r => {
      const svc = r.metric?.service || r.metric?.job || 'unknown';
      traffic[svc] = parseFloat(r.value?.[1] || 0);
    });
    return traffic;
  } catch (err) {
    console.error('[prometheus] fetch error:', err.message);
    return {};
  }
}

async function tick() {
  const [pods, traffic] = await Promise.all([getPods(), fetchTraffic()]);
  broadcast({ pods, events: getEvents(), traffic, timestamp: new Date().toISOString() });
}

subscribeAll();
setInterval(tick, 2000);
