const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
const zlib = require('zlib');

function generateHeader(messageType, specificFlags, serialization, compression) {
  return Buffer.from([ (0b0001 << 4) | 0b0001, (messageType << 4) | specificFlags, (serialization << 4) | compression, 0x00 ]);
}

module.exports = function setupSttWebSocket(server) {
  console.log("[WebSocket Setup] Initializing /api/stt path...");
  const wss = new WebSocket.Server({ server, path: '/api/stt' });
  const API_KEY = process.env.DOUBAO_SPEECH_TO_TXT_API;
  const WS_URL = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async";

  wss.on('connection', (clientWs) => {
    console.log("[WebSocket Connection] New client connected to STT endpoint");

    if (!API_KEY) {
      console.log("[WebSocket Error] Missing API_KEY. Closing client connection immediately.");
      return clientWs.close();
    }

    const requestId = uuidv4();
    console.log(`[STT Connection] Opening external WS to Volcengine (RequestId: ${requestId})...`);
    
    const volcWs = new WebSocket(WS_URL, {
      headers: { "X-Api-Key": API_KEY, "X-Api-Resource-Id": "volc.seedasr.sauc.duration", "X-Api-Request-Id": requestId, "X-Api-Sequence": "-1" }
    });

    let configSent = false;

    volcWs.on('open', () => {
      console.log(`[STT Connection] External WS connected. Sending initial config...`);
      const reqGzip = zlib.gzipSync(Buffer.from(JSON.stringify({
        user: { uid: "user_test" },
        audio: { format: "pcm", codec: "raw", rate: 16000, bits: 16, channel: 1, language: "zh-CN" },
        request: { model_name: "bigmodel", enable_nonstream: true }
      }), 'utf-8'));
      
      const size = Buffer.alloc(4);
      size.writeUInt32BE(reqGzip.length, 0);
      volcWs.send(Buffer.concat([generateHeader(1, 0, 1, 1), size, reqGzip]));
      configSent = true;
      console.log(`[STT Connection] Initial config sent successfully.`);
    });

    clientWs.on('message', (data, isBinary) => {
      if (!configSent || volcWs.readyState !== WebSocket.OPEN) {
        console.log("[STT Client Message] Received message but external WS not ready yet. Ignoring.");
        return;
      }
      
      const isStop = !isBinary && data.toString() === 'STOP';
      console.log(`[STT Client Message] Forwarding audio chunk. isStop flag: ${isStop}, data length: ${data.length}`);
      
      const chunkGzip = zlib.gzipSync(isStop ? Buffer.alloc(0) : data);
      const size = Buffer.alloc(4);
      size.writeUInt32BE(chunkGzip.length, 0);
      volcWs.send(Buffer.concat([generateHeader(2, isStop ? 2 : 0, 0, 1), size, chunkGzip]));
    });

    volcWs.on('message', (msg) => {
      if (msg.length < 8) return;

      const messageType = msg[1] >> 4;
      const specificFlags = msg[1] & 0x0F;
      const compression = msg[2] & 0x0F;

      let offset = 4; // Base header is 4 bytes

      // Check if 4-byte sequence number or 4-byte error code is present
      if (specificFlags === 1 || specificFlags === 3) {
        offset += 4; // Has Sequence number
      } else if (messageType === 15) {
        offset += 4; // Error response has an Error code
      }

      // Read payload size and advance offset
      const payloadSize = msg.readUInt32BE(offset);
      offset += 4;

      let payload = msg.subarray(offset, offset + payloadSize);

      if (compression === 1) { // Gzip compressed
        try { 
          payload = zlib.gunzipSync(payload); 
        } catch (e) {
          console.error("[STT External Message] Failed to gunzip payload:", e.message);
          return; 
        }
      }

      if (messageType === 15 && clientWs.readyState === WebSocket.OPEN) {
        console.error("[STT External Message] Received Error type frame:", payload.toString('utf-8'));
        return clientWs.send(JSON.stringify({ error: payload.toString('utf-8') }));
      }

      try {
        const resp = JSON.parse(payload.toString('utf-8'));
        if (resp.result?.text && clientWs.readyState === WebSocket.OPEN) {
          console.log("[STT External Message] Received valid text result, forwarding to client:", resp.result.text);
          clientWs.send(JSON.stringify({ text: resp.result.text }));
        }
      } catch (e) {
        console.error("[STT External Message] Failed to parse JSON response payload:", e.message);
      }
    });

    volcWs.on('close', () => {
      console.log("[STT Connection] External Volcengine WS closed. Closing client WS if open.");
      if (clientWs.readyState === WebSocket.OPEN) clientWs.close();
    });
    
    clientWs.on('close', () => {
      console.log("[WebSocket Connection] Client closed connection. Closing external WS if open.");
      if (volcWs.readyState === WebSocket.OPEN) volcWs.close();
    });
  });
};
