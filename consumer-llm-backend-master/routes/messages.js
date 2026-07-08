const express = require('express');
const router = express.Router();
const { redis } = require('../lib/redis');

const WEEK = 604800; 

router.get('/', async (req, res) => {
  console.log(`[Route: GET /api/messages] Invoked with query:`, req.query);
  const conversationId = req.query.conversationId;
  
  if (!conversationId) {
    console.log("[Route: GET /api/messages] No conversationId provided. Returning empty array.");
    return res.json([]);
  }

  console.log(`[Route: GET /api/messages] Fetching messages for conversation: ${conversationId}`);
  const rawMessages = await redis.hgetall(`msgs:${conversationId}`);
  
  if (!rawMessages || Object.keys(rawMessages).length === 0) {
    console.log(`[Route: GET /api/messages] No messages found for conversation: ${conversationId}`);
    return res.json([]);
  }

  console.log(`[Route: GET /api/messages] Found ${Object.keys(rawMessages).length} raw message(s). Parsing and sorting...`);
  const rows = Object.values(rawMessages)
    .map(m => typeof m === 'string' ? JSON.parse(m) : m)
    .sort((a, b) => a.created_at - b.created_at);

  console.log(`[Route: GET /api/messages] Returning ${rows.length} sorted message(s).`);
  res.json(rows);
});

router.delete('/', async (req, res) => {
  console.log(`[Route: DELETE /api/messages] Invoked with body:`, req.body);
  const { id } = req.body;
  
  console.log(`[Route: DELETE /api/messages] Searching for message ID: ${id} across all 'msgs:*' keys`);
  const keys = await redis.keys('msgs:*');
  
  for (const key of keys) {
    const rawMsg = await redis.hget(key, id);
    if (rawMsg) {
      console.log(`[Route: DELETE /api/messages] Found message ${id} in hash ${key}`);
      const msg = typeof rawMsg === 'string' ? JSON.parse(rawMsg) : rawMsg;
      const parentId = msg.parent_id;

      console.log(`[Route: DELETE /api/messages] Fetching all messages in ${key} to re-parent children...`);
      const allMsgs = await redis.hgetall(key);
      const pipeline = redis.pipeline();
      
      let reparentCount = 0;
      for (const [mId, mRaw] of Object.entries(allMsgs)) {
        const m = typeof mRaw === 'string' ? JSON.parse(mRaw) : mRaw;
        if (m.parent_id === id) {
          m.parent_id = parentId;
          pipeline.hset(key, mId, JSON.stringify(m));
          reparentCount++;
        }
      }
      
      console.log(`[Route: DELETE /api/messages] Re-parenting ${reparentCount} child message(s) to new parent ID: ${parentId}`);
      pipeline.hdel(key, id);
      console.log(`[Route: DELETE /api/messages] Executing deletion pipeline...`);
      await pipeline.exec();
      console.log(`[Route: DELETE /api/messages] Deletion complete.`);
      break;
    }
  }
  
  res.json({ success: true });
});

router.put('/', async (req, res) => {
  console.log(`[Route: PUT /api/messages] Invoked for editing message ID: ${req.body.id}`);
  const { id, content } = req.body;
  
  console.log(`[Route: PUT /api/messages] Searching across all 'msgs:*' keys for message ${id}`);
  const keys = await redis.keys('msgs:*');
  for (const key of keys) {
    const rawMsg = await redis.hget(key, id);
    if (rawMsg) {
      console.log(`[Route: PUT /api/messages] Found message ${id} in hash ${key}. Updating content.`);
      const msg = typeof rawMsg === 'string' ? JSON.parse(rawMsg) : rawMsg;
      msg.content = content;
      await redis.hset(key, id, JSON.stringify(msg));
      console.log(`[Route: PUT /api/messages] Content updated successfully.`);
      break;
    }
  }
  res.json({ success: true });
});

router.post('/', async (req, res) => {
  console.log(`[Route: POST /api/messages] Invoked with body containing ${req.body.messages?.length || 0} messages.`);
  const { messages } = req.body;
  
  if (Array.isArray(messages) && messages.length > 0) {
    const convId = messages[0].conversation_id;
    const key = `msgs:${convId}`;
    console.log(`[Route: POST /api/messages] Target hash key: ${key}`);
    
    const pipeline = redis.pipeline();
    for (const m of messages) {
      console.log(`[Route: POST /api/messages] Queuing insertion for message ID: ${m.id}`);
      pipeline.hset(key, m.id, JSON.stringify(m));
    }
    
    pipeline.expire(key, WEEK);
    console.log(`[Route: POST /api/messages] Executing Redis pipeline for insertions...`);
    await pipeline.exec();
    console.log(`[Route: POST /api/messages] Insertion pipeline complete.`);
  } else {
    console.log(`[Route: POST /api/messages] No valid messages array provided in request.`);
  }
  
  res.json({ success: true });
});

module.exports = router;
