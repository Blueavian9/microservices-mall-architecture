const http = require('http');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { connectNATS, drainNATS } = require('./events');
const { createRoutes } = require('./routes');
const { metricsMiddleware, register } = require('./middleware/metrics');

const app = express();

function allowedOrigins() {
  const raw = process.env.ALLOWED_ORIGINS;
  if (!raw) return false;
  const list = raw.split(',').map((s) => s.trim()).filter(Boolean);
  return list.length ? list : false;
}

async function main() {
  await connectNATS();

  app.use(helmet());

  app.use(
    cors({
      origin: allowedOrigins(),
    }),
  );

  app.use(morgan('combined'));
  app.use(metricsMiddleware);

  app.get('/health', (req, res) => {
    res.json({
      status: 'ok',
      service: 'api-gateway',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    });
  });

  app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  });

  createRoutes(app);

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
