const mongoose = require('mongoose');

const commentSchema = new mongoose.Schema({
  // Structure based on provided comment data
  'Douban Homepage': String,
  'Face Image Source': String,
  'Face Image Alt': String,
  'Reply Content': String,
  'Reply Time': String,
  'Image URL': String,
  'GIF URL': String,
  'Reply To Content': String,
  'Reply To Author': String,
}, { strict: false });


module.exports = commentSchema; // Export schema for dynamic model creation
