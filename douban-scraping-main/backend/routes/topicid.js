const express = require('express');
const router = express.Router();
const Discussion = require('../models/Discussion');

// GET all discussion IDs
router.get('/', async (req, res) => {
  try {
    // Select only the '_id' field for each discussion
    const discussionIds = await Discussion.find().select('_id');
    res.json(discussionIds);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;
