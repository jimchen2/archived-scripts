// app/src/main/java/com/example/consumerllm/model/Models.kt
package com.example.consumerllm.model

data class Message(
    val id: String,
    val parent_id: String?,
    val role: String,
    var content: String
)

data class Conversation(
    val id: String,
    val title: String
)

data class Settings(
    val model: String = "gemini-3.5-flash",
    val systemPrompt: String = ""
)
