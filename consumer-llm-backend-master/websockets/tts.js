// websockets/tts.js
const { WebSocketServer, WebSocket } = require('ws');
const { v4: uuidv4 } = require('uuid');

function setupTtsWebSocket(server) {
  const wss = new WebSocketServer({ noServer: true });

  server.on('upgrade', (request, socket, head) => {
    if (request.url === '/api/tts-stream') {
      wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
      });
    }
  });

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

    volcWs.on('open', () => {
      console.log('[TTS WS] Connected to Volcengine');
      // 1. 建立连接
      volcWs.send(JSON.stringify({ EventType: 'StartConnection' }));

      // 2. 创建会话 (默认参数)
      volcWs.send(JSON.stringify({
        EventType: 'StartSession',
        session_id: sessionId,
        req_params: {
          speaker: 'seed_tts_2_0_speaker', // 根据实际在控制台获取的音色ID替换
          audio_params: {
            format: 'pcm', // 推荐流式使用 pcm
            sample_rate: 24000
          }
        }
      }));
    });

    volcWs.on('message', (data) => {
      // 接收到火山引擎返回的流式音频/事件包，直接透传给前端客户端
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

    // 处理来自客户端的消息 (接收文字并发送给火山)
    clientWs.on('message', (message) => {
      try {
        const payload = JSON.parse(message);
        
        // 当客户端发送文本时触发 TaskRequest
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

