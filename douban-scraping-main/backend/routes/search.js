const express = require("express");
const mongoose = require("mongoose");
const router = express.Router();
const commentSchema = require("../models/Comment"); // Note: Adjust the path as necessary

const getCommentModel = (collectionName) => {
  // This creates a new model or retrieves the existing one with the same name
  return mongoose.models[collectionName] || mongoose.model(collectionName, commentSchema, collectionName);
};

router.get("/", async (req, res) => {
  const { query, discussion } = req.query; // Get the search and discussion query from the query parameters

  try {
    // Now we build our model based on the provided discussion name
    const model = getCommentModel(discussion);

    // Setup the MongoDB query
    const mongoQuery = {
      "data.Reply Content": { $regex: query, $options: "i" }, // Case-insensitive search
    };

    // Find matches
    const matches = await model.find(mongoQuery);

    // Return the result
    res.json(matches);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
