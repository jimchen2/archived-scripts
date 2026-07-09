const express = require('express');
const router = express.Router();
const { redis } = require('../lib/redis');

const WEEK = 604800; // 7 days in seconds

router.get('/', async (req, res) => {
  console.log("[Route: GET /api/conversations] Invoked");
  const offset = parseInt(req.query.offset || '0', 10);
  const limit = parseInt(req.query.limit || '10', 10);
  
  console.log(`[Route: GET /api/conversations] Fetching conv index offset: ${offset}, limit: ${limit}`);

  // Get conversation IDs sorted by newest first
  const convIds = await redis.zrevrange('conversations:index', offset, offset + limit - 1);
  console.log(`[Route: GET /api/conversations] Found ${convIds.length} conversation(s)`);
  
  if (convIds.length === 0) return res.json([]);

  const pipeline = redis.pipeline();
  convIds.forEach(id => pipeline.hgetall(`conv:${id}`));
  
  console.log("[Route: GET /api/conversations] Executing Redis pipeline for conv details...");
  const results = await pipeline.exec();

  const rows = results.map(([err, data]) => data).filter(Boolean);
  res.json(rows);
});

router.post('/', async (req, res) => {
  console.log("[Route: POST /api/conversations] Invoked with body:", req.body);
  const { id, title } = req.body;
  const now = Date.now();

  const pipeline = redis.pipeline();
  pipeline.zadd('conversations:index', now, id);
  pipeline.hset(`conv:${id}`, { id, title: title || 'New Conversation', created_at: now });
  
  // Set 1 week expiration
  pipeline.expire('conversations:index', WEEK);
  pipeline.expire(`conv:${id}`, WEEK);
  
  console.log(`[Route: POST /api/conversations] Executing Redis pipeline to create conv:${id}`);
  await pipeline.exec();
  res.json({ success: true });
});

router.delete('/', async (req, res) => {
  console.log("[Route: DELETE /api/conversations] Invoked with body:", req.body);
  const { id } = req.body;
  
  const pipeline = redis.pipeline();
  pipeline.zrem('conversations:index', id);
  pipeline.del(`conv:${id}`);
  pipeline.del(`msgs:${id}`);
  
  console.log(`[Route: DELETE /api/conversations] Executing Redis pipeline to delete conv:${id}`);
  await pipeline.exec();

  res.json({ success: true });
});

module.exports = router;
