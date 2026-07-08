const express = require('express');
const router = express.Router();
const { redis } = require('../lib/redis');
const { callLLM } = require('../lib/llm');

const WEEK = 604800;

router.post('/', async (req, res) => {
  console.log("[Route: POST /api/chat] Invoked with body keys:", Object.keys(req.body));
  
  const { messages, userMsgId, botMsgId, parentId, conversationId, apiKey, model } = req.body;
  const userMsg = messages.length > 0 ? messages[messages.length - 1] : null;
  const msgKey = `msgs:${conversationId}`;
  
  console.log(`[Route: POST /api/chat] Processing for Conversation ID: ${conversationId}, Bot Msg ID: ${botMsgId}`);

  const pipeline = redis.pipeline();

  if (userMsg && userMsg.role === "user" && userMsgId) {
    console.log(`[Route: POST /api/chat] Saving user message ${userMsgId} to Redis`);
    pipeline.hset(msgKey, userMsgId, JSON.stringify({
      id: userMsgId, conversation_id: conversationId, parent_id: parentId,
      role: "user", content: userMsg.content, created_at: Date.now()
    }));
  }

  const botPayload = {
    id: botMsgId, conversation_id: conversationId, parent_id: userMsgId || parentId,
    role: "assistant", content: "", created_at: Date.now() + 1
  };
  
  pipeline.hset(msgKey, botMsgId, JSON.stringify(botPayload));
  pipeline.expire(msgKey, WEEK);
  pipeline.expire('conversations:index', WEEK);
  pipeline.expire(`conv:${conversationId}`, WEEK);
  
  console.log("[Route: POST /api/chat] Executing initial Redis pipeline...");
  await pipeline.exec();
  console.log("[Route: POST /api/chat] Initial Redis pipeline executed successfully");

  process.nextTick(async () => {
    console.log(`[Route: POST /api/chat] Background LLM call starting for botMsgId: ${botMsgId}`);
    let finalContent = "";
    await callLLM({
      apiKey, model, messages,
      onChunk: async (chunk) => {
        // Warning: This might log A LOT. If it's too much, remove this specific chunk log.
        console.log(`[LLM Chunk] Received chunk for ${botMsgId}, length: ${chunk.length}`);
        finalContent += chunk;
        await redis.publish(`msg:${botMsgId}:channel`, JSON.stringify(chunk));
      },
      onDone: async () => {
        console.log(`[LLM Done] Finished stream for ${botMsgId}. Total length: ${finalContent.length}`);
        botPayload.content = finalContent;
        await redis.hset(msgKey, botMsgId, JSON.stringify(botPayload));
        await redis.publish(`msg:${botMsgId}:channel`, "[DONE]");
      },
      onError: async (err) => {
        console.error(`[LLM Error] Error for ${botMsgId}:`, err.message);
        botPayload.content = finalContent + `\n\n[Error: ${err.message}]`;
        await redis.hset(msgKey, botMsgId, JSON.stringify(botPayload));
        await redis.publish(`msg:${botMsgId}:channel`, JSON.stringify(`\n\n[Error: ${err.message}]`));
        await redis.publish(`msg:${botMsgId}:channel`, "[DONE]");
      },
    });
  });

  res.json({ success: true });
});

module.exports = router;
