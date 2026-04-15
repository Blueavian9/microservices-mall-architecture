const http = require('http');
const { validate } = require('./env.validate');
const { connectNATS, drainNATS } = require('./middleware/nats.client');
const { createApp } = require('./app');

async function main() {
  validate();
  await connectNATS();

  const app = createApp();
  const port = Number(process.env.PORT) || 3000;
  const server = http.createServer(app);

  server.listen(port, () => {
    console.info(`api-gateway listening on port ${port}`);
  });

  const shutdown = () => {
    console.info('SIGTERM received; shutting down gracefully');
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
