// routes/auth.js
const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');

require('dotenv').config();
const secret = process.env.JWT_SECRET;

router.get('/', (req, res) => {
  const token = req.headers.authorization; // Get the token from the request headers

  if (token) {
    try {
      const decoded = jwt.verify(token, secret); // Verify the token
      res.json({ authenticated: true, user: decoded });
    } catch (err) {
      res.json({ authenticated: false });
    }
  } else {
    res.json({ authenticated: false });
  }
});

module.exports = router;