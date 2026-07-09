const express = require('express');
const router = express.Router();
const { redis } = require('../lib/redis'); // adjust path if needed

const SETTINGS_KEY = "app:global:settings";

router.get('/', async (req, res) => {
  console.log(`[Route: GET /api/settings] Invoked. Fetching from key: ${SETTINGS_KEY}`);
  try {
    const settingsStr = await redis.get(SETTINGS_KEY);
    if (settingsStr) {
      console.log(`[Route: GET /api/settings] Found existing settings in Redis.`);
      res.json(JSON.parse(settingsStr));
    } else {
      console.log(`[Route: GET /api/settings] No settings found in Redis. Returning empty object.`);
      res.json({});
    }
  } catch (err) {
    console.error(`[Route: GET /api/settings] Error fetching settings:`, err.message);
    res.status(500).json({ error: "Failed to load settings" });
  }
});

router.post('/', async (req, res) => {
  console.log(`[Route: POST /api/settings] Invoked with body keys:`, Object.keys(req.body));
  try {
    const { apiKey = "", model = "gemini-3.5-flash", systemPrompt = "" } = req.body;
    console.log(`[Route: POST /api/settings] Saving model: ${model}, API Key present: ${!!apiKey}`);
    
    await redis.set(SETTINGS_KEY, JSON.stringify({ apiKey, model, systemPrompt }));
    console.log(`[Route: POST /api/settings] Successfully saved settings to ${SETTINGS_KEY}`);
    
    res.json({ success: true });
  } catch (err) {
    console.error(`[Route: POST /api/settings] Error saving settings:`, err.message);
    res.status(500).json({ error: "Failed to save settings" });
  }
});

module.exports = router;
