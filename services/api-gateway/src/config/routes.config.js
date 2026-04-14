/**
 * Add new downstream services here only — do not edit router.js.
 * mountPath: URL prefix on this gateway (e.g. /auth → proxied to target + path).
 * targetEnv: name of process.env key holding the upstream base URL.
 * methods: HTTP methods allowed through this proxy (lowercase).
 */
module.exports = [
  {
    mountPath: '/auth',
    targetEnv: 'AUTH_SERVICE_URL',
    methods: ['GET', 'POST'],
  },
  {
    mountPath: '/booking',
    targetEnv: 'BOOKING_SERVICE_URL',
    methods: ['GET', 'POST'],
  },
];
