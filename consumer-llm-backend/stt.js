// server.js
require('dotenv').config({ path: '.env' });
const http = require('http');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
const zlib = require('zlib');

// === CONFIG ===
const API_KEY = process.env.DOUBAO_API; 
const RESOURCE_ID = "volc.seedasr.sauc.duration";
const WS_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async";
const PORT = process.env.PORT || 3001; 
// ==============

function generateHeader(messageType, specificFlags, serialization, compression) {
  const version = 0b0001;
  const headerSize = 0b0001;
  const byte0 = (version << 4) | headerSize;
  const byte1 = (messageType << 4) | specificFlags;
  const byte2 = (serialization << 4) | compression;
  const byte3 = 0x00;
  return Buffer.from([byte0, byte1, byte2, byte3]);
}

// Simple HTTP server to attach the WebSocket server to
const server = http.createServer((req, res) => {
  res.writeHead(200);
  res.end('Volcengine WebSocket Proxy Server is running\n');
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (clientWs) => {
  console.log("[WS Backend] Browser connected");

  if (!API_KEY) {
    console.error("[WS Backend] Error: DOUBAO_API is not set in .env");
    clientWs.send(JSON.stringify({ error: "Server missing API Key" }));
    clientWs.close();
    return;
  }

  const reqId = uuidv4();
  const volcWs = new WebSocket(WS_URL, {
    headers: {
      "X-Api-Key": API_KEY,
      "X-Api-Resource-Id": RESOURCE_ID,
      "X-Api-Request-Id": reqId,
      "X-Api-Sequence": "-1"
    }
  });

  let configSent = false;

  volcWs.on('open', () => {
    console.log("[WS Backend] Connected to Volcengine");
    
    // 1. Send Full Client Request (config)
    const reqJson = {
      user: { uid: "user_test" },
      audio: {
        format: "pcm",   // raw PCM streamed from browser
        codec: "raw",
        rate: 16000,
        bits: 16,
        channel: 1,
        language: "zh-CN"
      },
      request: {
        model_name: "bigmodel",
        enable_nonstream: true
      }
    };

    const reqGzip = zlib.gzipSync(Buffer.from(JSON.stringify(reqJson), 'utf-8'));
    const header = generateHeader(1, 0, 1, 1);
    const size = Buffer.alloc(4);
    size.writeUInt32BE(reqGzip.length, 0);
    volcWs.send(Buffer.concat([header, size, reqGzip]));

    configSent = true;
  });

  // 2. Receive messages from the Browser
  clientWs.on('message', (data, isBinary) => {
    if (!configSent || volcWs.readyState !== WebSocket.OPEN) return;

    // text message "STOP" -> send last (negative) packet
    if (!isBinary && data.toString() === 'STOP') {
      console.log("[WS Backend] Received STOP from browser, sending last packet");
      const chunkGzip = zlib.gzipSync(Buffer.alloc(0));
      const header = generateHeader(2, 2, 0, 1); // flag 2 = last packet
      const size = Buffer.alloc(4);
      size.writeUInt32BE(chunkGzip.length, 0);
      volcWs.send(Buffer.concat([header, size, chunkGzip]));
      return;
    }

    // normal audio chunk (Binary PCM)
    const chunkGzip = zlib.gzipSync(data);
    const header = generateHeader(2, 0, 0, 1);
    const size = Buffer.alloc(4);
    size.writeUInt32BE(chunkGzip.length, 0);
    volcWs.send(Buffer.concat([header, size, chunkGzip]));
  });

  // 3. Receive results from Volcengine -> push live to browser
  volcWs.on('message', (message) => {
    if (message.length < 12) return;
    const messageType = message[1] >> 4;
    const payloadSize = message.readUInt32BE(8);
    let payload = message.subarray(12, 12 + payloadSize);

    // Decompress payload if necessary
    if ((message[2] & 0x0F) === 1) {
      try { payload = zlib.gunzipSync(payload); } catch (e) { return; }
    }

    // Handle Volcengine API error
    if (messageType === 15) {
      const errText = payload.toString('utf-8');
      console.error("[WS Backend] API Error:", errText);
      if (clientWs.readyState === WebSocket.OPEN) {
        clientWs.send(JSON.stringify({ error: errText }));
      }
      return;
    }

    // Parse success response and send text back to browser
    try {
      const resp = JSON.parse(payload.toString('utf-8'));
      if (resp.result && resp.result.text !== undefined) {
        if (clientWs.readyState === WebSocket.OPEN) {
          clientWs.send(JSON.stringify({ text: resp.result.text }));
        }
      }
    } catch (e) { /* ignore non-JSON */ }
  });

  // Cleanups
  volcWs.on('close', () => {
    console.log("[WS Backend] Volcengine connection closed");
    if (clientWs.readyState === WebSocket.OPEN) clientWs.close();
  });

  volcWs.on('error', (err) => {
    console.error("[WS Backend] Volcengine error:", err.message);
    if (clientWs.readyState === WebSocket.OPEN) {
      clientWs.send(JSON.stringify({ error: err.message }));
    }
  });

  clientWs.on('close', () => {
    console.log("[WS Backend] Browser disconnected");
    if (volcWs.readyState === WebSocket.OPEN) volcWs.close();
  });

  clientWs.on('error', (err) => {
    console.error("[WS Backend] Browser WS error:", err.message);
  });
});

server.listen(PORT, () => {
  console.log(`[WS Backend] Server running on ws://localhost:${PORT}`);
});
