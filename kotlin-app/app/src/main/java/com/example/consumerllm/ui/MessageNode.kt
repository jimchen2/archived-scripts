// app/src/main/java/com/example/consumerllm/ui/MessageNode.kt
package com.example.consumerllm.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.consumerllm.model.Message
import dev.jeziellago.compose.markdowntext.MarkdownText

@Composable
fun MessageNode(
    msg: Message,
    modelName: String,
    onCopy: (String) -> Unit,
    onDelete: (String) -> Unit,
    onRead: () -> Unit // <--- ADD THIS
) {
    val isUser = msg.role == "user"
    val backgroundColor = if (isUser) Color(0xFFF8F9FA) else Color.Transparent

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        colors = CardDefaults.cardColors(containerColor = backgroundColor),
        shape = RoundedCornerShape(8.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isUser) 1.dp else 0.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = if (isUser) "You" else modelName,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF6C757D)
                )
            }

            // Body
            MarkdownText(
                markdown = msg.content.ifEmpty { "*(typing...)*" },
                fontSize = 16.sp,
                color = MaterialTheme.colorScheme.onSurface
            )

            // Footer (Actions)
            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                horizontalArrangement = Arrangement.End
            ) {
                // UPDATE THIS BUTTON
                TextButton(onClick = onRead) { Text("Read", fontSize = 12.sp, color = Color(0xFF6C757D)) }
                TextButton(onClick = { onCopy(msg.content) }) { Text("Copy", fontSize = 12.sp, color = Color(0xFF6C757D)) }
                TextButton(onClick = { onDelete(msg.id) }) { Text("Delete", fontSize = 12.sp, color = Color.Red) }
            }
        }
    }
}
