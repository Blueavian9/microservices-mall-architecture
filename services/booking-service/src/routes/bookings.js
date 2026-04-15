const { Router } = require('express');
const { query } = require('../db');
const { publishEvent } = require('../nats');

const router = Router();

// POST /booking/create
router.post('/create', async (req, res) => {
  const { user_id, service_name } = req.body;
  if (!user_id || !service_name) {
    return res.status(400).json({ error: 'user_id and service_name required' });
  }
  try {
    const result = await query(
      'INSERT INTO bookings (user_id, service_name, status) VALUES ($1, $2, $3) RETURNING *',
      [user_id, service_name, 'pending']
    );
    const booking = result.rows[0];
    await publishEvent('booking.created', {
      event_id: String(booking.id),
      booking_id: booking.id,
      user_id: booking.user_id,
      service_name: booking.service_name,
      timestamp: new Date().toISOString(),
    });
    res.status(201).json(booking);
  } catch (err) {
    console.error('booking create error:', err);
    res.status(500).json({ error: 'internal server error' });
  }
});

// GET /booking/list
router.get('/list', async (req, res) => {
  const { user_id } = req.query;
  try {
    const result = user_id
      ? await query('SELECT * FROM bookings WHERE user_id=$1 ORDER BY created_at DESC', [user_id])
      : await query('SELECT * FROM bookings ORDER BY created_at DESC');
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: 'internal server error' });
  }
});

// DELETE /booking/cancel/:id
router.delete('/cancel/:id', async (req, res) => {
  try {
    const result = await query(
      'UPDATE bookings SET status=$1 WHERE id=$2 RETURNING *',
      ['cancelled', req.params.id]
    );
    if (!result.rows.length) return res.status(404).json({ error: 'not found' });
    await publishEvent('booking.cancelled', {
      booking_id: result.rows[0].id,
      user_id: result.rows[0].user_id,
      timestamp: new Date().toISOString(),
    });
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: 'internal server error' });
  }
});

module.exports = router;
