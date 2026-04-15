const { createProxyMiddleware } = require('http-proxy-middleware');
const routesConfig = require('../config/routes.config');
const { publishEvent } = require('../middleware/nats.client');

/**
 * Mounts all proxies from routes.config.js. Targets must exist (enforced by env.validate).
 */
function applyProxyRoutes(app) {
  for (const def of routesConfig) {
    const target = process.env[def.targetEnv];
    if (!target) {
      throw new Error(`Missing ${def.targetEnv} — run env.validate() before applyProxyRoutes`);
    }

    const methodSet = new Set(def.methods.map((m) => m.toUpperCase()));

    const proxy = createProxyMiddleware({
      target,
      changeOrigin: true,
      pathFilter: (pathname, req) => methodSet.has(req.method),
      on: {
        proxyReq: (proxyReq, req) => {
          publishEvent('request.received', {
            method: req.method,
            path: req.originalUrl || req.url,
            target,
            timestamp: new Date().toISOString(),
          });
        },
      },
    });

    app.use(def.mountPath, proxy);
  }
}

module.exports = { applyProxyRoutes };
