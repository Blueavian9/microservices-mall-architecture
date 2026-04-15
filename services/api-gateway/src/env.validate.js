/**
 * Fail fast on missing required configuration (before HTTP listen).
 * NATS is optional — gateway runs without the bus for local/unit tests.
 */
const REQUIRED_STRINGS = [
  ['AUTH_SERVICE_URL', 'Upstream auth service base URL'],
  ['BOOKING_SERVICE_URL', 'Upstream booking service base URL'],
  ['ALLOWED_ORIGINS', 'Comma-separated CORS origins'],
];

function validate() {
  const missing = [];
  for (const [key] of REQUIRED_STRINGS) {
    const v = process.env[key];
    if (v === undefined || String(v).trim() === '') {
      missing.push(key);
    }
  }
  if (missing.length) {
    throw new Error(
      `Missing required environment variables: ${missing.join(', ')}. See .env.example.`,
    );
  }
}

module.exports = { validate };
