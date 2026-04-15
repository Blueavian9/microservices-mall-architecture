const { Pool } = require('pg');

let pool;

async function initDB() {
  pool = new Pool({ connectionString: process.env.DATABASE_URL });
  await pool.query(`
    CREATE TABLE IF NOT EXISTS bookings (
      id SERIAL PRIMARY KEY,
      user_id TEXT NOT NULL,
      service_name TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `);
  console.info('DB pool ready + bookings table ensured');
}

async function query(text, params) {
  return pool.query(text, params);
}

module.exports = { initDB, query };
