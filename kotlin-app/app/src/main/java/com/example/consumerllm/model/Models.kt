// app/src/main/java/com/example/consumerllm/model/Models.kt
package com.example.consumerllm.model

import com.google.gson.annotations.SerializedName

data class Message(
    val id: String,
    @SerializedName(value = "parent_id", alternate = ["parentId"])
    val parent_id: String?,
    val role: String,
    var content: String,
    @SerializedName(value = "created_at", alternate = ["createdAt"])
    val created_at: Long? = null
)

data class Conversation(
    val id: String,
    val title: String
)

data class Settings(
    val model: String = "gemini-3.5-flash",
    val systemPrompt: String = ""
)
