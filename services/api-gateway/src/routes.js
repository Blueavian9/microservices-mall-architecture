const { createProxyMiddleware } = require('http-proxy-middleware');
const { publishEvent } = require('./events');

function createRoutes(app) {
  const authTarget = process.env.AUTH_SERVICE_URL;
  const bookingTarget = process.env.BOOKING_SERVICE_URL;

  if (!authTarget) {
    console.warn('AUTH_SERVICE_URL is not set');
  }
  if (!bookingTarget) {
    console.warn('BOOKING_SERVICE_URL is not set');
  }

  const authProxy = createProxyMiddleware({
    target: authTarget,
    changeOrigin: true,
    pathFilter: (pathname, req) => req.method === 'POST',
    on: {
      proxyReq: (proxyReq, req) => {
        publishEvent('request.received', {
          method: req.method,
          path: req.originalUrl || req.url,
          target: authTarget,
          timestamp: new Date().toISOString(),
        });
      },
    },
  });

  const bookingProxy = createProxyMiddleware({
    target: bookingTarget,
    changeOrigin: true,
    pathFilter: (pathname, req) => req.method === 'POST' || req.method === 'GET',
    on: {
      proxyReq: (proxyReq, req) => {
        publishEvent('request.received', {
          method: req.method,
          path: req.originalUrl || req.url,
          target: bookingTarget,
          timestamp: new Date().toISOString(),
        });
      },
    },
  });

  app.use('/auth', authProxy);
  app.use('/booking', bookingProxy);
}

module.exports = { createRoutes };
