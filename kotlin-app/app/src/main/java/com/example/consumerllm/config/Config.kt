// app/src/main/java/com/example/consumerllm/config/Config.kt
package com.example.consumerllm.config

object Config {
    // Main API backend endpoint
    const val API_BASE = "https://consumer-llm-backend.onrender.com"
    
    // STT (Speech-to-Text) WebSocket endpoint
    // Ensure it starts with ws:// or wss://
    const val STT_WS_URL = "wss://consumer-llm-backend-1.onrender.com"
    
    // TTS (Text-to-Speech) WebSocket endpoint
    // Update this to wherever you deploy your tts.js proxy
    const val TTS_WS_URL = "wss://consumer-llm-tts.onrender.com/" 
}
