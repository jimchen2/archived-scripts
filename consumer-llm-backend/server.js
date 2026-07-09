// server.js
require("dotenv").config();
const http = require("http");
const express = require("express");
const cors = require("cors");

console.log("[Backend] Initializing server...");

// Import our route handlers
const chatRoute = require("./routes/chat");
const chatstreamRoute = require("./routes/chatstream");
const settingsRoute = require("./routes/settings");
const conversationsRoute = require("./routes/conversations");
const messagesRoute = require("./routes/messages");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Add a global middleware to log every single HTTP request
app.use((req, res, next) => {
  console.log(`[HTTP Request] ${req.method} ${req.url}`);
  next();
});

// Mount HTTP routes
app.use("/api/chat", chatRoute);
app.use("/api/chatstream", chatstreamRoute);
app.use("/api/settings", settingsRoute);
app.use("/api/conversations", conversationsRoute);
app.use("/api/messages", messagesRoute);

// Create HTTP server
const server = http.createServer(app);

// Start listening
server.listen(PORT, () => {
  console.log(`[Backend] HTTP API running on http://localhost:${PORT}`);
});
