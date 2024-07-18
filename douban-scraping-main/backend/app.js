const express = require('express');
const cors = require('cors'); // Import cors
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const path = require('path'); // Import path
const fs = require('fs'); // Import fs

const discussionsRouter = require('./routes/discussions');
const commentsRouter = require('./routes/comments');
const topicsRouter = require('./routes/topics');
const topicsId = require('./routes/topicid');
const search = require('./routes/search');

const app = express();
const port = 5000;

// Use cors middleware to allow cross-origin requests
app.use(cors());

mongoose.connect('mongodb://localhost/douban', { useNewUrlParser: true, useUnifiedTopology: true });

app.use(bodyParser.json());

app.use('/api/discussions', discussionsRouter);
app.use('/api/comments', commentsRouter);
app.use('/api/topics', topicsRouter);
app.use('/api/topicid', topicsId);
app.use('/api/search', search);

// Serve static files from the "media" directory
app.use('/media', express.static(path.join(__dirname, '../media')));

app.get('/listmedia', (req, res) => {
  fs.readdir(path.join(__dirname, '../media'), (err, files) => {
    if (err) {
      res.status(500).json({ error: err });
    } else {
      res.json(files);
    }
  });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
