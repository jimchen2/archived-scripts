// app/src/main/java/com/example/consumerllm/ui/ChatInput.kt
package com.example.consumerllm.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun ChatInput(
    inputText: String,
    onInputTextChanged: (String) -> Unit,
    onSend: (String) -> Unit,
    isRecording: Boolean,
    isProcessing: Boolean,
    statusText: String,
    onToggleRecording: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(10.dp),
        verticalAlignment = Alignment.Bottom
    ) {
        // Record Button
        Button(
            onClick = onToggleRecording,
            enabled = !isProcessing || isRecording,
            modifier = Modifier.padding(end = 8.dp),
            shape = RoundedCornerShape(8.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = if (isRecording) Color(0xFFDC3545) else Color(0xFF6C757D)
            )
        ) {
            if (isProcessing && !isRecording) {
                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(24.dp), strokeWidth = 2.dp)
            } else {
                Text(if (isRecording) "⏹" else "🎤", color = Color.White)
            }
        }

        // Input Field
        OutlinedTextField(
            value = inputText,
            onValueChange = onInputTextChanged,
            placeholder = { Text(if (isRecording) statusText else "输入消息...") },
            enabled = !isRecording && !isProcessing,
            modifier = Modifier
                .weight(1f)
                .heightIn(min = 50.dp, max = 120.dp),
            shape = RoundedCornerShape(8.dp)
        )

        // Send Button
        Button(
            onClick = {
                if (inputText.isNotBlank()) {
                    onSend(inputText)
                }
            },
            modifier = Modifier.padding(start = 8.dp),
            shape = RoundedCornerShape(8.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0D6EFD))
        ) {
            Text("发送", color = Color.White, fontWeight = FontWeight.Bold)
        }
    }
}