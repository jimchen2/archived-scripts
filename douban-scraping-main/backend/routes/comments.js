const express = require("express");
const router = express.Router();
const mongoose = require("mongoose");
const commentSchema = require("../models/Comment");

// Middleware to set the model for the specific comments collection
router.use("/:collectionId", (req, res, next) => {
  const collectionName = `comments.${req.params.collectionId}`;
  req.CommentModel = mongoose.model(
    collectionName,
    commentSchema,
    collectionName
  );
  next();
});

// GET comments from a specific collection
router.get("/:collectionId", async (req, res) => {
  if (req.query.start !== undefined) {
    const limit = 500; // specify pagination limit
    const start = parseInt(req.query.start); // get start request

    const comments = await req.CommentModel.find()
      .where("numericId")
      .gte(start)
      .sort({ numericId: 1 })
      .limit(limit);
    res.json(comments);
  } else {
    const comments = await req.CommentModel.find().sort({ numericId: 1 });
    res.json(comments);
  }
});

// POST a new comment to a specific collection
router.post("/:collectionId", async (req, res) => {
  const comment = new req.CommentModel(req.body);
  await comment.save();
  res.status(201).json(comment);
});

module.exports = router;
