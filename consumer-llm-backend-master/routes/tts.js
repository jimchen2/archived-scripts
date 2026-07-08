const express = require('express');
const router = express.Router();
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const APP_ID = process.env.DOUBAO_APP_ID;
const ACCESS_KEY = process.env.DOUBAO_ACCESS_TOKEN;
const APP_KEY = process.env.DOUBAO_APP_KEY || "PlgvMymc7f3tQnJ6"; // Add this to your .env
const RESOURCE_ID = "volc.speech.dialog";
const WS_URL = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue";

function generateHeader(messageType, specificFlags, serialization, compression) {
    const byte0 = (1 << 4) | 1;
    const byte1 = (messageType << 4) | specificFlags;
    const byte2 = (serialization << 4) | compression;
    const byte3 = 0x00;
    return Buffer.from([byte0, byte1, byte2, byte3]);
}

router.post('/', async (req, res) => {
    try {
        const { text } = req.body;
        if (!text) return res.status(400).json({ error: "Text is required" });

        const audioBuffer = await new Promise((resolve, reject) => {
            const connectId = uuidv4();
            const sessionId = uuidv4();
            const headers = {
                "X-Api-App-ID": APP_ID,
                "X-Api-Access-Key": ACCESS_KEY,
                "X-Api-Resource-Id": RESOURCE_ID,
                "X-Api-App-Key": APP_KEY,
                "X-Api-Connect-Id": connectId
            };

            const ws = new WebSocket(WS_URL, { headers });
            let audioChunks = [];

            function sendSessionEvent(eventId, jsonPayload) {
                const header = generateHeader(1, 0b0100, 1, 0);
                const eventBuffer = Buffer.alloc(4);
                eventBuffer.writeUInt32BE(eventId, 0);
                
                const sessionStrBuffer = Buffer.from(sessionId);
                const sessionLenBuffer = Buffer.alloc(4);
                sessionLenBuffer.writeUInt32BE(sessionStrBuffer.length, 0);
                
                const payloadBuffer = Buffer.from(JSON.stringify(jsonPayload));
                const payloadLenBuffer = Buffer.alloc(4);
                payloadLenBuffer.writeUInt32BE(payloadBuffer.length, 0);

                ws.send(Buffer.concat([header, eventBuffer, sessionLenBuffer, sessionStrBuffer, payloadLenBuffer, payloadBuffer]));
            }

            ws.on('open', () => {
                const header = generateHeader(1, 0b0100, 1, 0);
                const eventBuffer = Buffer.alloc(4);
                eventBuffer.writeUInt32BE(1, 0); 
                const payload = Buffer.from("{}");
                const sizeBuffer = Buffer.alloc(4);
                sizeBuffer.writeUInt32BE(payload.length, 0);
                ws.send(Buffer.concat([header, eventBuffer, sizeBuffer, payload]));
            });

            ws.on('message', (data) => {
                if (data.length < 8) return;
                const specificFlags = data[1] & 0x0F;
                let offset = 4;
                let eventId = -1;
                
                if (specificFlags === 0b0100) {
                    eventId = data.readUInt32BE(offset);
                    offset += 4;
                }
                
                let payloadSize = 0;
                let payload = Buffer.alloc(0);

                if (eventId === 50 || eventId === 51) {
                    payloadSize = data.readUInt32BE(offset);
                    offset += 4;
                    payload = data.subarray(offset, offset + payloadSize);
                } else if (eventId > 0) {
                    const sessionLen = data.readUInt32BE(offset);
                    offset += 4 + sessionLen; 
                    payloadSize = data.readUInt32BE(offset);
                    offset += 4;
                    payload = data.subarray(offset, offset + payloadSize);
                }

                if (eventId === 50) { 
                    sendSessionEvent(100, {
                        dialog: { extra: { model: "1.2.1.1", input_mod: "text" } },
                        tts: { audio_config: { format: "ogg" } } 
                    });
                } else if (eventId === 150) { 
                    sendSessionEvent(501, { content: "a" }); // Trigger flow
                } else if (eventId === 553) { 
                    // Send exact text chunked appropriately
                    sendSessionEvent(500, { start: true, content: text, end: false });
                    sendSessionEvent(500, { start: false, content: "", end: true });
                } else if (eventId === 352) { 
                    audioChunks.push(payload);
                } else if (eventId === 359) { 
                    sendSessionEvent(102, {}); 
                } else if (eventId === 152) { 
                    ws.close();
                    resolve(Buffer.concat(audioChunks));
                } else if (eventId === 599) { 
                    reject(new Error(payload.toString('utf-8')));
                }
            });

            ws.on('error', reject);
        });

        res.set({
            'Content-Type': 'audio/ogg',
            'Content-Disposition': 'attachment; filename="speech.ogg"'
        });
        res.send(audioBuffer);

    } catch (error) {
        console.error("TTS Error:", error);
        res.status(500).json({ error: "Failed to generate speech" });
    }
});

module.exports = router;

