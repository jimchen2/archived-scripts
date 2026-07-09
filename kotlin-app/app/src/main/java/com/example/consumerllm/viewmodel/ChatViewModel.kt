// app/src/main/java/com/example/consumerllm/viewmodel/ChatViewModel.kt
package com.example.consumerllm.viewmodel

import android.Manifest
import android.app.Application
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.AudioTrack
import android.media.MediaRecorder
import androidx.core.app.ActivityCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.consumerllm.config.Config
import com.example.consumerllm.model.Conversation
import com.example.consumerllm.model.Message
import com.example.consumerllm.model.Settings
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import okio.ByteString
import okio.ByteString.Companion.toByteString
import java.util.UUID

class ChatViewModel(application: Application) : AndroidViewModel(application) {

    private val client = OkHttpClient()
    private val gson = Gson()
    private val prefs = application.getSharedPreferences("llm_settings", Context.MODE_PRIVATE)

    private val _conversations = MutableStateFlow<List<Conversation>>(emptyList())
    val conversations = _conversations.asStateFlow()

    private val _activeConversation = MutableStateFlow<String?>(null)
    val activeConversation = _activeConversation.asStateFlow()

    // Map of messageId to Message
    private val _messages = MutableStateFlow<Map<String, Message>>(emptyMap())
    val messages = _messages.asStateFlow()

    private val _currentId = MutableStateFlow<String?>(null)
    
    private val _settings = MutableStateFlow(Settings())
    val settings = _settings.asStateFlow()

    private val _isLoadingConv = MutableStateFlow(false)
    val isLoadingConv = _isLoadingConv.asStateFlow()
    
    private val _hasMoreConv = MutableStateFlow(true)
    val hasMoreConv = _hasMoreConv.asStateFlow()

    // STT (Voice Recognition) state variables
    private var sttWebSocket: WebSocket? = null
    private var audioRecord: AudioRecord? = null
    private var recordingJob: Job? = null

    private val _recognizedText = MutableStateFlow("")
    val recognizedText = _recognizedText.asStateFlow()

    // TTS (Text-to-Speech) state variables
    private var ttsWebSocket: WebSocket? = null
    private var audioTrack: AudioTrack? = null

    init {
        initData()
    }

    private fun initData() {
        loadConversations(0)
    }

    fun updateSettings(newSettings: Settings) {
        _settings.value = newSettings
    }

    fun saveSettings() {
        loadConversations(0)
    }

    fun loadConversations(offset: Int = 0) {
        viewModelScope.launch(Dispatchers.IO) {
            _isLoadingConv.value = true
            try {
                val request = Request.Builder()
                    .url("${Config.API_BASE}/api/conversations?offset=$offset&limit=10")
                    .build()

                client.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        val body = response.body?.string()
                        val type = object : TypeToken<List<Conversation>>() {}.type
                        val data: List<Conversation> = gson.fromJson(body, type)
                        
                        withContext(Dispatchers.Main) {
                            val current = if (offset == 0) emptyList() else _conversations.value
                            _conversations.value = current + data
                            _hasMoreConv.value = data.size == 10
                        }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                _isLoadingConv.value = false
            }
        }
    }

    fun loadMessages(convId: String) {
        viewModelScope.launch(Dispatchers.IO) {
            try {
                val request = Request.Builder()
                    .url("${Config.API_BASE}/api/messages?conversationId=$convId")
                    .build()

                client.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        val body = response.body?.string()
                        val type = object : TypeToken<List<Message>>() {}.type
                        val data: List<Message> = gson.fromJson(body, type)
                        
                        val msgMap = data.associateBy { it.id }
                        withContext(Dispatchers.Main) {
                            _messages.value = msgMap
                            _currentId.value = data.lastOrNull()?.id
                            _activeConversation.value = convId
                        }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun handleNewChat() {
        _activeConversation.value = null
        _messages.value = emptyMap()
        _currentId.value = null
        stopTTS() // Stop any ongoing TTS if user starts a new chat
    }

    fun getActivePath(): List<Message> {
        val path = mutableListOf<Message>()
        var curr = _currentId.value
        val map = _messages.value
        
        while (curr != null && map.containsKey(curr)) {
            val msg = map[curr]!!
            path.add(0, msg)
            curr = msg.parent_id
        }
        return path
    }
    
    fun deleteConversation(id: String) {
        viewModelScope.launch(Dispatchers.IO) {
            withContext(Dispatchers.Main) {
                _conversations.value = _conversations.value.filter { it.id != id }
                if (_activeConversation.value == id) {
                    handleNewChat()
                }
            }
            try {
                val jsonMediaType = "application/json; charset=utf-8".toMediaType()
                val payload = mapOf("id" to id)
                val requestBody = gson.toJson(payload).toRequestBody(jsonMediaType)

                val request = Request.Builder()
                    .url("${Config.API_BASE}/api/conversations")
                    .delete(requestBody)
                    .build()

                client.newCall(request).execute()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
    
    fun deleteMessage(msgId: String) {
        viewModelScope.launch(Dispatchers.IO) {
            val currentMap = _messages.value.toMutableMap()
            val deletedMsg = currentMap.remove(msgId)
            
            if (deletedMsg != null) {
                val newParentId = deletedMsg.parent_id
                currentMap.entries.forEach { (key, msg) ->
                    if (msg.parent_id == msgId) {
                        currentMap[key] = msg.copy(parent_id = newParentId)
                    }
                }
                withContext(Dispatchers.Main) {
                    _messages.value = currentMap
                    if (_currentId.value == msgId) {
                        _currentId.value = newParentId
                    }
                }
            }

            try {
                val jsonMediaType = "application/json; charset=utf-8".toMediaType()
                val payload = mapOf("id" to msgId)
                val requestBody = gson.toJson(payload).toRequestBody(jsonMediaType)

                val request = Request.Builder()
                    .url("${Config.API_BASE}/api/messages")
                    .delete(requestBody)
                    .build()

                client.newCall(request).execute()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun sendMessage(text: String) {
        if (text.isBlank()) return

        // Stop previous audio playback/TTS streams if still running
        stopTTS()

        val convId = _activeConversation.value ?: UUID.randomUUID().toString()
        val isNewConv = _activeConversation.value == null
        val parentId = _currentId.value
        val userMsgId = UUID.randomUUID().toString()
        val botMsgId = UUID.randomUUID().toString()

        val newMap = _messages.value.toMutableMap()
        newMap[userMsgId] = Message(id = userMsgId, parent_id = parentId, role = "user", content = text)
        newMap[botMsgId] = Message(id = botMsgId, parent_id = userMsgId, role = "assistant", content = "")
        
        _messages.value = newMap
        _currentId.value = botMsgId

        if (isNewConv) {
            val title = text.take(30)
            _activeConversation.value = convId
            _conversations.value = listOf(Conversation(convId, title)) + _conversations.value
            
            viewModelScope.launch(Dispatchers.IO) {
                try {
                    val jsonMediaType = "application/json; charset=utf-8".toMediaType()
                    val payload = mapOf("id" to convId, "title" to title)
                    val requestBody = gson.toJson(payload).toRequestBody(jsonMediaType)
                    val req = Request.Builder()
                        .url("${Config.API_BASE}/api/conversations")
                        .post(requestBody)
                        .build()
                    client.newCall(req).execute()
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }

        val jsonMediaType = "application/json; charset=utf-8".toMediaType()
        
        val path = getActivePath()
            .filter { it.id != botMsgId }
            .map { mapOf("role" to it.role, "content" to it.content) }
        
        viewModelScope.launch(Dispatchers.IO) {
            try {
                // --- Initialize AudioTrack for real-time TTS Playback ---
                val sampleRate = 24000
                val bufferSize = AudioTrack.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)
                audioTrack = AudioTrack.Builder()
                    .setAudioAttributes(AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build())
                    .setAudioFormat(AudioFormat.Builder()
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(sampleRate)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build())
                    .setBufferSizeInBytes(bufferSize)
                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .build()
                audioTrack?.play()

                // --- Open WebSocket to TTS Proxy Backend ---
                val ttsReq = Request.Builder().url(Config.TTS_WS_URL).build()
                ttsWebSocket = client.newWebSocket(ttsReq, object : WebSocketListener() {
                    override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                        // We received raw PCM bytes from the backend! Stream directly to speaker.
                        val audioBytes = bytes.toByteArray()
                        audioTrack?.write(audioBytes, 0, audioBytes.size)
                    }

                    override fun onMessage(webSocket: WebSocket, text: String) {
                        // Handle JSON control messages (e.g., done or errors)
                        try {
                            val json = gson.fromJson(text, Map::class.java)
                            if (json["done"] == true) {
                                // Synthesis complete, let the AudioTrack drain
                                audioTrack?.stop()
                            }
                        } catch (e: Exception) { e.printStackTrace() }
                    }

                    override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                        stopTTS()
                    }
                    
                    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                        t.printStackTrace()
                        stopTTS()
                    }
                })

                // --- Start LLM SSE Stream ---
                val sseReq = Request.Builder()
                    .url("${Config.API_BASE}/api/chatstream?id=$botMsgId")
                    .build()
                
                val factory = EventSources.createFactory(client)
                factory.newEventSource(sseReq, object : EventSourceListener() {
                    override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
                        if (data == "[DONE]") {
                            ttsWebSocket?.send("STOP") // Tell TTS backend we finished sending text
                            eventSource.cancel()
                            return
                        }
                        
                        val chunk = try {
                            gson.fromJson(data, String::class.java)
                        } catch (e: Exception) {
                            data
                        }
                        
                        // Pass chunk to our TTS backend immediately
                        if (chunk.isNotBlank()) {
                            ttsWebSocket?.send(chunk)
                        }
                        
                        val currentMap = _messages.value.toMutableMap()
                        val currentMsg = currentMap[botMsgId]
                        if (currentMsg != null) {
                            currentMap[botMsgId] = currentMsg.copy(content = currentMsg.content + chunk)
                            _messages.value = currentMap
                        }
                    }
                })

                val payload = mapOf(
                    "messages" to path,
                    "userMsgId" to userMsgId,
                    "botMsgId" to botMsgId,
                    "parentId" to parentId,
                    "conversationId" to convId,
                    "model" to _settings.value.model
                )
                val requestBody = gson.toJson(payload).toRequestBody(jsonMediaType)
                
                val chatReq = Request.Builder()
                    .url("${Config.API_BASE}/api/chat")
                    .post(requestBody)
                    .build()
                
                client.newCall(chatReq).execute()

            } catch (e: Exception) {
                e.printStackTrace()
                stopTTS()
            }
        }
    }

    fun readMessage(text: String) {
        if (text.isBlank()) return
        stopTTS()

        viewModelScope.launch(Dispatchers.IO) {
            try {
                // Initialize AudioTrack for real-time TTS Playback
                val sampleRate = 24000
                val bufferSize = AudioTrack.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)
                audioTrack = AudioTrack.Builder()
                    .setAudioAttributes(AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_MEDIA)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build())
                    .setAudioFormat(AudioFormat.Builder()
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(sampleRate)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build())
                    .setBufferSizeInBytes(bufferSize)
                    .setTransferMode(AudioTrack.MODE_STREAM)
                    .build()
                audioTrack?.play()

                // Open WebSocket to TTS Proxy Backend
                val ttsReq = Request.Builder().url(Config.TTS_WS_URL).build()
                ttsWebSocket = client.newWebSocket(ttsReq, object : WebSocketListener() {
                    override fun onOpen(webSocket: WebSocket, response: Response) {
                        // Send the full text to the TTS proxy, then immediately send STOP to close the task stream
                        webSocket.send(text)
                        webSocket.send("STOP")
                    }

                    override fun onMessage(webSocket: WebSocket, bytes: ByteString) {
                        val audioBytes = bytes.toByteArray()
                        audioTrack?.write(audioBytes, 0, audioBytes.size)
                    }

                    override fun onMessage(webSocket: WebSocket, text: String) {
                        try {
                            val json = gson.fromJson(text, Map::class.java)
                            if (json["done"] == true) {
                                audioTrack?.stop()
                            }
                        } catch (e: Exception) { e.printStackTrace() }
                    }

                    override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                        stopTTS()
                    }

                    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                        t.printStackTrace()
                        stopTTS()
                    }
                })
            } catch (e: Exception) {
                e.printStackTrace()
                stopTTS()
            }
        }
    }

    private fun stopTTS() {
        try {
            ttsWebSocket?.close(1000, "User stopped/Chat updated")
            ttsWebSocket = null
            
            audioTrack?.let {
                if (it.state == AudioTrack.STATE_INITIALIZED) {
                    it.stop()
                    it.release()
                }
            }
            audioTrack = null
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    // --- Voice Recognition (STT) logic ---

    fun startRecording(context: Context) {
        if (ActivityCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            return
        }

        _recognizedText.value = ""
        stopTTS() // Prevent playback clash while recording

        val wsUrl = Config.STT_WS_URL
        
        val request = Request.Builder().url(wsUrl).build()
        sttWebSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = gson.fromJson(text, Map::class.java)
                    val textChunk = json["text"] as? String ?: ""
                    _recognizedText.value = textChunk
                } catch (e: Exception) {
                    _recognizedText.value = text
                }
            }
        })

        val sampleRate = 16000
        val channelConfig = AudioFormat.CHANNEL_IN_MONO
        val audioFormat = AudioFormat.ENCODING_PCM_16BIT
        val bufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)

        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            channelConfig,
            audioFormat,
            bufferSize
        )

        audioRecord?.startRecording()

        recordingJob = viewModelScope.launch(Dispatchers.IO) {
            val buffer = ByteArray(bufferSize)
            while (isActive) {
                val read = audioRecord?.read(buffer, 0, buffer.size) ?: 0
                if (read > 0) {
                    sttWebSocket?.send(buffer.copyOfRange(0, read).toByteString())
                }
            }
        }
    }

    fun stopRecording() {
        try {
            recordingJob?.cancel()
            recordingJob = null
            
            audioRecord?.takeIf { it.state == AudioRecord.STATE_INITIALIZED }?.let {
                it.stop()
                it.release()
            }
            audioRecord = null
            
            sttWebSocket?.send("STOP")
            sttWebSocket?.close(1000, "User stopped recording") 
            sttWebSocket = null
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    override fun onCleared() {
        super.onCleared()
        stopRecording()
        stopTTS()
    }
}
