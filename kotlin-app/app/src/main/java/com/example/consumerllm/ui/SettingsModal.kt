// app/src/main/java/com/example/consumerllm/ui/SettingsModal.kt
package com.example.consumerllm.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties

@Composable
fun SettingsModal(
    show: Boolean,
    model: String,
    systemPrompt: String,
    onHide: () -> Unit,
    onModelChange: (String) -> Unit,
    onSystemPromptChange: (String) -> Unit,
    onSave: () -> Unit
) {
    if (!show) return

    Dialog(
        onDismissRequest = onHide,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = Color.White
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 20.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("设置 (Settings)", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    TextButton(onClick = onHide) {
                        Text("关闭", color = Color(0xFF0D6EFD), fontSize = 16.sp)
                    }
                }

                // Body
                Column(modifier = Modifier.weight(1f)) {
                    Text("模型 (Model)", fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 6.dp))
                    OutlinedTextField(
                        value = model,
                        onValueChange = onModelChange,
                        placeholder = { Text("例如: gemini-1.5-pro") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 16.dp),
                        shape = RoundedCornerShape(8.dp)
                    )

                    Text("系统提示词 (System Prompt)", fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 6.dp))
                    OutlinedTextField(
                        value = systemPrompt,
                        onValueChange = onSystemPromptChange,
                        placeholder = { Text("你是一个有用的助手。") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(120.dp),
                        shape = RoundedCornerShape(8.dp),
                        maxLines = 5
                    )
                }

                // Footer
                Button(
                    onClick = { onSave() },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF198754))
                ) {
                    Text("保存设置", color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
