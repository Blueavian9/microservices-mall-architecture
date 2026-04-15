const express = require('express');
const helmet = require('helmet');
const morgan = require('morgan');
const { register, metricsMiddleware } = require('./metrics');
const bookingRouter = require('./routes/bookings');

function createApp() {
  const app = express();
  app.use(helmet());
  app.use(morgan('combined'));
  app.use(express.json());
  app.use(metricsMiddleware);

  app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'booking-service', timestamp: new Date().toISOString() });
  });

  app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  });

  app.use('/booking', bookingRouter);
  return app;
}

module.exports = { createApp };
