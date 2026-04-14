const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { metricsMiddleware, register } = require('./metrics/metrics');
const { applyProxyRoutes } = require('./routes/router');

function allowedOrigins() {
  const raw = process.env.ALLOWED_ORIGINS;
  if (!raw) return false;
  const list = raw.split(',').map((s) => s.trim()).filter(Boolean);
  return list.length ? list : false;
}

/**
 * Express app factory — no listen(); used by index.js and tests.
 */
function createApp() {
  const app = express();

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

  applyProxyRoutes(app);

  return app;
}

module.exports = { createApp };
