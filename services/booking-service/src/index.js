require('dotenv').config();
const http = require('http');
const { connectNATS, drainNATS } = require('./nats');
const { initDB } = require('./db');
const { createApp } = require('./app');

async function main() {
  await initDB();
  await connectNATS();
  const app = createApp();
  const port = Number(process.env.PORT) || 3002;
  const server = http.createServer(app);
  server.listen(port, () => {
    console.info(`booking-service listening on port ${port}`);
  });
  const shutdown = async () => {
    server.close(async () => {
      await drainNATS();
      process.exit(0);
    });
  };
  process.on('SIGTERM', shutdown);
}

main().catch((err) => {
  console.error('Fatal startup error:', err);
  process.exit(1);
});
