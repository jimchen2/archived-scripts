// tts.js
require('dotenv').config();
const WebSocket = require('ws');
const http = require('http');

const PORT = process.env.PORT || 3000;
const MINIMAX_API_KEY = process.env.MINIMAX_API;

if (!MINIMAX_API_KEY) {
    console.error("Error: MINIMAX_API_KEY environment variable is missing.");
    process.exit(1);
}

// Create an HTTP server to attach the WebSocket server
const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end('TTS Proxy Server is running.\n');
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (clientWs) => {
    console.log('Android client connected');

    let isMinimaxReady = false;
    let textQueue = [];

    // Connect to MiniMax WebSocket API
    const minimaxWs = new WebSocket('wss://api.minimax.io/ws/v1/t2a_v2', {
        headers: {
            'Authorization': `Bearer ${MINIMAX_API_KEY}`
        }
    });

    minimaxWs.on('open', () => {
        console.log('Connected to MiniMax API');
    });

    minimaxWs.on('message', (data) => {
        try {
            const response = JSON.parse(data.toString());

            if (response.event === 'connected_success') {
                // Initialize the task with Android-compatible audio settings
                const startMsg = {
                    event: "task_start",
                    model: "speech-2.8-hd",
                    voice_setting: {
                        voice_id: "male-qn-qingse",
                        speed: 1,
                        vol: 1,
                        pitch: 0,
                        english_normalization: false
                    },
                    audio_setting: {
                        sample_rate: 24000, // Matches AudioTrack in Android
                        bitrate: 128000,
                        format: "pcm",      // Matches ENCODING_PCM_16BIT
                        channel: 1          // Matches CHANNEL_OUT_MONO
                    }
                };
                minimaxWs.send(JSON.stringify(startMsg));
            } 
            else if (response.event === 'task_started') {
                isMinimaxReady = true;
                console.log('MiniMax task started');
                // Send any buffered text chunks
                while (textQueue.length > 0) {
                    const text = textQueue.shift();
                    sendTextToMinimax(text);
                }
            } 
            else if (response.event === 'task_failed') {
                console.error(`Task Failed: ${response.base_resp?.status_msg}`);
                clientWs.send(JSON.stringify({ error: response.base_resp?.status_msg }));
            }
            
            // Handle incoming audio data
            if (response.data && response.data.audio) {
                // MiniMax returns audio as hex strings; convert to binary buffer
                const audioBuffer = Buffer.from(response.data.audio, 'hex');
                // Send raw PCM binary data back to the Android client
                if (clientWs.readyState === WebSocket.OPEN) {
                    clientWs.send(audioBuffer); 
                }
            }

            if (response.is_final) {
                console.log('MiniMax task completed');
                if (clientWs.readyState === WebSocket.OPEN) {
                    clientWs.send(JSON.stringify({ done: true }));
                }
            }

        } catch (err) {
            console.error('Error parsing MiniMax response:', err);
        }
    });

    minimaxWs.on('close', () => {
        console.log('MiniMax connection closed');
        if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.close();
        }
    });

    minimaxWs.on('error', (err) => {
        console.error('MiniMax WS Error:', err);
    });

    // Handle messages (text chunks) from Android Client
    clientWs.on('message', (message) => {
        const text = message.toString();
        console.log('Received from Android:', text);

        if (text === "STOP") {
            // End the task
            if (minimaxWs.readyState === WebSocket.OPEN) {
                minimaxWs.send(JSON.stringify({ event: "task_finish" }));
            }
        } else {
            // Forward text to MiniMax
            if (isMinimaxReady) {
                sendTextToMinimax(text);
            } else {
                textQueue.push(text); // Buffer if MiniMax hasn't confirmed task_start yet
            }
        }
    });

    clientWs.on('close', () => {
        console.log('Android client disconnected');
        if (minimaxWs.readyState === WebSocket.OPEN) {
            minimaxWs.send(JSON.stringify({ event: "task_finish" }));
            minimaxWs.close();
        }
    });

    function sendTextToMinimax(text) {
        if (minimaxWs.readyState === WebSocket.OPEN) {
            minimaxWs.send(JSON.stringify({
                event: "task_continue",
                text: text
            }));
        }
    }
});

server.listen(PORT, () => {
    console.log(`TTS WebSocket Proxy listening on port ${PORT}`);
});
