// websockets/tts.js
const { WebSocketServer, WebSocket } = require('ws');
const { v4: uuidv4 } = require('uuid');

function setupTtsWebSocket(server) {
  // 1. Change this line to use { server, path }
  const wss = new WebSocketServer({ server, path: '/api/tts-stream' });

  wss.on('connection', (clientWs) => {
    console.log('[TTS WS] Client connected');
    const connectId = uuidv4();
    const sessionId = uuidv4();

    const apiKey = process.env.DOUBAO_API || ''; 
    const resourceId = 'seed-tts-2.0';
    
    const volcengineWsUrl = 'wss://openspeech.bytedance.com/api/v3/tts/bidirection';

    const volcWs = new WebSocket(volcengineWsUrl, {
      headers: {
        'X-Api-Key': apiKey,
        'X-Api-Resource-Id': resourceId,
        'X-Api-Connect-Id': connectId
      }
    });

    // ... (Keep all your existing volcWs and clientWs logic here exactly as is)
    volcWs.on('open', () => {
      console.log('[TTS WS] Connected to Volcengine');
      volcWs.send(JSON.stringify({ EventType: 'StartConnection' }));
      volcWs.send(JSON.stringify({
        EventType: 'StartSession',
        session_id: sessionId,
        req_params: {
          speaker: 'seed_tts_2_0_speaker',
          audio_params: {
            format: 'pcm',
            sample_rate: 24000
          }
        }
      }));
    });

    volcWs.on('message', (data) => {
      if (clientWs.readyState === WebSocket.OPEN) {
        clientWs.send(data);
      }
    });

    volcWs.on('close', () => {
      console.log('[TTS WS] Volcengine connection closed');
      if (clientWs.readyState === WebSocket.OPEN) {
        clientWs.close();
      }
    });

    volcWs.on('error', (err) => {
      console.error('[TTS WS] Volcengine Error:', err);
    });

    clientWs.on('message', (message) => {
      try {
        const payload = JSON.parse(message);
        if (payload.action === 'synthesize' && payload.text) {
          volcWs.send(JSON.stringify({
            EventType: 'TaskRequest',
            session_id: sessionId,
            text: payload.text
          }));
        } else if (payload.action === 'stop') {
          volcWs.send(JSON.stringify({ EventType: 'FinishSession' }));
          volcWs.send(JSON.stringify({ EventType: 'FinishConnection' }));
        }
      } catch (err) {
        console.error('[TTS WS] Failed to parse client message:', err);
      }
    });

    clientWs.on('close', () => {
      console.log('[TTS WS] Client disconnected');
      if (volcWs.readyState === WebSocket.OPEN) {
        volcWs.send(JSON.stringify({ EventType: 'FinishSession' }));
        volcWs.send(JSON.stringify({ EventType: 'FinishConnection' }));
        volcWs.close();
      }
    });
  });
}

module.exports = setupTtsWebSocket;
