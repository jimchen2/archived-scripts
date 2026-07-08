const express = require('express');
const router = express.Router();
const { redisSubscriber } = require('../lib/redis');

router.get('/', (req, res) => {
  console.log(`[Route: GET /api/chatstream] Invoked with query:`, req.query);
  const id = req.query.id;
  
  if (!id) {
    console.error("[Route: GET /api/chatstream] Error: Missing message ID");
    return res.status(400).send('Missing message ID');
  }

  console.log(`[Route: GET /api/chatstream] Setting up SSE response for message ID: ${id}`);
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });

  const targetChannel = `msg:${id}:channel`;
  
  const handler = (incomingChannel, message) => {
    if (incomingChannel !== targetChannel) return;
    
    if (message === '[DONE]') {
      console.log(`[Route: GET /api/chatstream] Received [DONE] signal for ${id}. Closing stream.`);
      cleanup();
      return res.end();
    }
    
    // Log length of chunk rather than content to prevent massive terminal spam, 
    // but you can change this to `console.log(message)` if you want to see the text.
    console.log(`[Route: GET /api/chatstream] Streaming chunk for ${id}, length: ${message.length}`);
    res.write(`data: ${message}\n\n`);
  };
  
  const cleanup = () => {
    console.log(`[Route: GET /api/chatstream] Cleaning up Redis subscription for channel: ${targetChannel}`);
    redisSubscriber.unsubscribe(targetChannel);
    redisSubscriber.removeListener('message', handler);
  };

  req.on('close', () => {
    console.log(`[Route: GET /api/chatstream] Client closed connection early for message ID: ${id}`);
    cleanup();
  });

  console.log(`[Route: GET /api/chatstream] Subscribing to Redis channel: ${targetChannel}`);
  redisSubscriber.subscribe(targetChannel, (err) => {
    if (err) {
      console.error(`[Route: GET /api/chatstream] Failed to subscribe to channel ${targetChannel}:`, err);
      return res.end();
    }
    console.log(`[Route: GET /api/chatstream] Successfully subscribed to ${targetChannel}. Waiting for messages...`);
    redisSubscriber.on('message', handler);
  });
});

module.exports = router;
