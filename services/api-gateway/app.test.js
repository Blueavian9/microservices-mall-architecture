const request = require('supertest');
const { validate } = require('./src/env.validate');
const { createApp } = require('./src/app');

describe('api-gateway', () => {
  let app;

  beforeAll(() => {
    process.env.AUTH_SERVICE_URL = 'http://127.0.0.1:39991';
    process.env.BOOKING_SERVICE_URL = 'http://127.0.0.1:39992';
    process.env.ALLOWED_ORIGINS = 'http://localhost:5173';
    delete process.env.NATS_URL;
    validate();
    app = createApp();
  });

  it('GET /health returns ok payload', async () => {
    const res = await request(app).get('/health').expect(200);
    expect(res.body).toMatchObject({
      status: 'ok',
      service: 'api-gateway',
    });
    expect(res.body).toHaveProperty('timestamp');
    expect(typeof res.body.uptime).toBe('number');
  });

  it('GET /metrics returns Prometheus text', async () => {
    const res = await request(app).get('/metrics').expect(200);
    expect(res.headers['content-type']).toMatch(/text/);
    expect(res.text).toContain('http_requests_total');
  });

  it('GET /not-a-route returns 404', async () => {
    await request(app).get('/not-a-route').expect(404);
  });

  it('applies helmet security headers', async () => {
    const res = await request(app).get('/health').expect(200);
    expect(res.headers['x-content-type-options']).toBe('nosniff');
  });
});
