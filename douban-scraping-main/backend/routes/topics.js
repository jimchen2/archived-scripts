const express = require("express");
const router = express.Router();
const mongoose = require("mongoose");
const Topic = require("../models/Topic"); // Ensure this schema is defined in your models

// GET all topics
router.get("/", async (req, res) => {
  const topics = await Topic.find();
  res.send(topics);
});

// Middleware for handling operations on specific topics by dataId
router.use("/:dataId", async (req, res, next) => {
  // Assuming dataId is used to identify a specific document
  // Adjust logic here based on how dataId should be used
  // This middleware might set up req.topicDocument for use in specific routes
  // For now, let's just pass through to the route handlers
  next();
});

// GET a specific topic by dataId
router.get("/:dataId", async (req, res) => {
  try {
    const dataId = req.params.dataId;

    const topic = await Topic.findOne({
      Link: { $regex: dataId, $options: "i" },
    });

    if (!topic) {
      return res.status(404).json({ message: "Topic not found" });
    }
    res.json(topic);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// POST a new topic to a specific dataId
// Assuming this means updating an existing topic or adding a new one if not found
router.post("/:dataId", async (req, res) => {
  try {
    let topic = await Topic.findById(req.params.dataId);
    if (topic) {
      // Update existing topic
      Object.assign(topic, req.body);
      await topic.save();
    } else {
      // Create new topic if one doesn't exist with the specified dataId
      topic = new Topic({ _id: req.params.dataId, ...req.body }); // Ensure _id is handled correctly
      await topic.save();
    }
    res.send(topic);
  } catch (error) {
    // Handle possible errors
    res.status(500).send(error.message);
  }
});

module.exports = router;
