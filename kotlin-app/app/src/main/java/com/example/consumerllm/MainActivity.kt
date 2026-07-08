// app/src/main/java/com/example/consumerllm/MainActivity.kt
package com.example.consumerllm

import android.Manifest
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.consumerllm.ui.ChatInput
import com.example.consumerllm.ui.MessageNode
import com.example.consumerllm.ui.SettingsModal
import com.example.consumerllm.ui.Sidebar
import com.example.consumerllm.viewmodel.ChatViewModel
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private val viewModel: ChatViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                MainAppScreen(viewModel)
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainAppScreen(viewModel: ChatViewModel) {
    val context = LocalContext.current
    val conversations by viewModel.conversations.collectAsState()
    val activeConversation by viewModel.activeConversation.collectAsState()
    val settings by viewModel.settings.collectAsState()
    val isLoadingConv by viewModel.isLoadingConv.collectAsState()
    val hasMoreConv by viewModel.hasMoreConv.collectAsState()
    
    // We re-calculate the active path whenever messages or currentId changes
    val messagesMap by viewModel.messages.collectAsState()
    val activePath = remember(messagesMap) { viewModel.getActivePath() }

    var showSettings by remember { mutableStateOf(false) }
    var inputText by remember { mutableStateOf("") }
    var isRecording by remember { mutableStateOf(false) }

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val clipboardManager = LocalClipboardManager.current
    val listState = rememberLazyListState()

    // --- Voice Recognition Logic ---
    val recognizedText by viewModel.recognizedText.collectAsState()
    
    // Update the input field in real-time as the backend streams transcribed text back
    LaunchedEffect(recognizedText) {
        if (isRecording && recognizedText.isNotEmpty()) {
            inputText = recognizedText
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            isRecording = true
            viewModel.startRecording(context)
        }
    }

    val handleToggleRecording = {
        if (isRecording) {
            isRecording = false
            viewModel.stopRecording()
        } else {
            // Clear existing text when starting a new recording, or append to it if you prefer
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
        }
    }
    // ---------------------------------

    // Auto-scroll to bottom when new messages arrive
    LaunchedEffect(activePath.size) {
        if (activePath.isNotEmpty()) {
            listState.animateScrollToItem(activePath.size - 1)
        }
    }

    // Sidebar Composable wrapper
    val sidebarContent = @Composable {
        Sidebar(
            conversations = conversations,
            activeConversationId = activeConversation,
            isLoading = isLoadingConv,
            hasMore = hasMoreConv,
            onNewChat = {
                viewModel.handleNewChat()
                scope.launch { drawerState.close() }
            },
            onSelectConversation = { id ->
                viewModel.loadMessages(id)
                scope.launch { drawerState.close() }
            },
            onDeleteConversation = { /* Implement delete */ },
            onShowSettings = { showSettings = true },
            onLoadMore = { viewModel.loadConversations(conversations.size) }
        )
    }

    BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
        val isLargeScreen = maxWidth > 768.dp

        if (isLargeScreen) {
            // Desktop/Tablet layout
            Row(modifier = Modifier.fillMaxSize()) {
                Box(modifier = Modifier.width(280.dp).fillMaxHeight()) {
                    sidebarContent()
                }
                Box(modifier = Modifier.weight(1f).fillMaxHeight()) {
                    ChatContent(
                        activePath = activePath,
                        listState = listState,
                        modelName = settings.model,
                        inputText = inputText,
                        isRecording = isRecording,
                        onInputTextChanged = { inputText = it },
                        onSend = {
                            viewModel.sendMessage(it)
                            inputText = ""
                        },
                        onToggleRecording = handleToggleRecording,
                        onCopy = { clipboardManager.setText(AnnotatedString(it)) },
                        onDeleteMessage = { id -> viewModel.deleteMessage(id) },
                        onOpenMenu = null // No menu button on large screens
                    )
                }
            }
        } else {
            // Mobile layout using ModalNavigationDrawer
            ModalNavigationDrawer(
                drawerState = drawerState,
                drawerContent = {
                    ModalDrawerSheet(modifier = Modifier.width(300.dp)) {
                        sidebarContent()
                    }
                }
            ) {
                ChatContent(
                    activePath = activePath,
                    listState = listState,
                    modelName = settings.model,
                    inputText = inputText,
                    isRecording = isRecording,
                    onInputTextChanged = { inputText = it },
                    onSend = {
                        viewModel.sendMessage(it)
                        inputText = ""
                    },
                    onToggleRecording = handleToggleRecording,
                    onCopy = { clipboardManager.setText(AnnotatedString(it)) },
                    onDeleteMessage = { id -> viewModel.deleteMessage(id) },
                    onOpenMenu = { scope.launch { drawerState.open() } }
                )
            }
        }
    }

    // Settings Modal
    SettingsModal(
        show = showSettings,
        model = settings.model,
        systemPrompt = settings.systemPrompt,
        onHide = { showSettings = false },
        onModelChange = { viewModel.updateSettings(settings.copy(model = it)) },
        onSystemPromptChange = { viewModel.updateSettings(settings.copy(systemPrompt = it)) },
        onSave = {
            viewModel.saveSettings()
            showSettings = false
        }
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatContent(
    activePath: List<com.example.consumerllm.model.Message>,
    listState: androidx.compose.foundation.lazy.LazyListState,
    modelName: String,
    inputText: String,
    isRecording: Boolean,
    onInputTextChanged: (String) -> Unit,
    onSend: (String) -> Unit,
    onToggleRecording: () -> Unit,
    onCopy: (String) -> Unit,
    onDeleteMessage: (String) -> Unit,
    onOpenMenu: (() -> Unit)?
) {
    Scaffold(
        topBar = {
            if (onOpenMenu != null) {
                TopAppBar(
                    title = { Text("Chat", fontWeight = FontWeight.Bold) },
                    navigationIcon = {
                        IconButton(onClick = onOpenMenu) {
                            Text("☰", fontSize = 24.sp)
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.White)
                )
            }
        },
        bottomBar = {
            ChatInput(
                inputText = inputText,
                onInputTextChanged = onInputTextChanged,
                onSend = onSend,
                isRecording = isRecording,
                isProcessing = false,
                statusText = "Listening...",
                onToggleRecording = onToggleRecording
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(Color(0xFFF8F9FA))
        ) {
            if (activePath.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("按住下面说话", fontSize = 20.sp, color = Color(0xFF6C757D))
                }
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp)
                ) {
                    items(activePath, key = { it.id }) { msg ->
                        MessageNode(
                            msg = msg,
                            modelName = modelName,
                            onCopy = onCopy,
                            onDelete = onDeleteMessage
                        )
                    }
                }
            }
        }
    }
}
