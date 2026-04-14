const promClient = require('prom-client');

const register = new promClient.Registry();
promClient.collectDefaultMetrics({ register });

const httpRequestsTotal = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register],
});

const httpRequestDurationMs = new promClient.Histogram({
  name: 'http_request_duration_ms',
  help: 'HTTP request duration in milliseconds',
  labelNames: ['method', 'route'],
  buckets: [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
  registers: [register],
});

function routeLabel(req) {
  if (req.route && req.route.path) return req.route.path;
  return req.path || 'unknown';
}

function metricsMiddleware(req, res, next) {
  const start = Date.now();
  const method = req.method;
  const route = routeLabel(req);

  res.on('finish', () => {
    const durationMs = Date.now() - start;
    const statusCode = String(res.statusCode);
    httpRequestsTotal.inc({ method, route, status_code: statusCode });
    httpRequestDurationMs.observe({ method, route }, durationMs);
  });

  next();
}

module.exports = { metricsMiddleware, register };
