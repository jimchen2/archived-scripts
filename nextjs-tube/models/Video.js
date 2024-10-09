const mongoose = require("mongoose");

const SubtitleSchema = new mongoose.Schema({
  language: { type: String, required: true },
  url: { type: String, required: true },
});

const VideoSchema = new mongoose.Schema({
  tags: { type: [String], default: [] },
  language: { type: String, required: true },
  filename: { type: String, required: true },
  previewVideoUrl: { type: String, required: true },
  previewImageUrl: { type: String, required: true },
  isMerged: { type: Boolean, required: true },
  createdAt: { type: Date, default: Date.now },

  uploadedVideo: {
    s3ObjectKey: String,
    videoUrl: String,
    subtitles: [SubtitleSchema],
    previewImageTimestamp: { type: Number },
    previewVideoStart: { type: Number },
    previewVideoEnd: { type: Number },
  },

  mergedVideo: {
    platform: String,
    externalUrl: String,
  },
});

// Indexes for efficient querying
VideoSchema.index({ tags: 1 });
VideoSchema.index({ filename: "text" });
VideoSchema.index({ language: 1 });
VideoSchema.index({ createdAt: -1 });

const Video = mongoose.models.Video || mongoose.model("Video", VideoSchema);

module.exports = Video;
