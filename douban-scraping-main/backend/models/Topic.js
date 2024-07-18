const mongoose = require('mongoose');

const topicSchema = new mongoose.Schema({
  'User Profile URL': String,
  'User Image Source': String,
  'User Image Alt Text': String,
  'Post Time': Date,
  'Main Content': String,
  'Link': String,
});

const Topic = mongoose.model('Topic', topicSchema);

module.exports = Topic;
