const express = require('express');
const router = express.Router();
const Discussion = require('../models/Discussion');

// GET all discussions
router.get('/', async (req, res) => {
  const discussions = await Discussion.find();
  res.json(discussions);
});

// POST a new discussion
router.post('/', async (req, res) => {
  const discussion = new Discussion(req.body);
  await discussion.save();
  res.status(201).json(discussion);
});

module.exports = router;
