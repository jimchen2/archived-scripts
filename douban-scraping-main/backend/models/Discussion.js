const mongoose = require('mongoose');

const discussionSchema = new mongoose.Schema({
  // Assuming structure based on provided data
  title: String,
  content: String,
  author: String,
  createdAt: Date,
});

const Discussion = mongoose.model('Discussion', discussionSchema);

module.exports = Discussion;
