import dbConnect from '../../lib/mongoose';
import Video from '../../models/Video';

export default async (req, res) => {
  await dbConnect();

  if (req.method === 'GET') {
    const { id } = req.query;

    if (!id) {
      return res.status(400).json({ error: 'Video ID is required' });
    }

    try {
      const video = await Video.findById(id);

      if (!video) {
        return res.status(404).json({ error: 'Video not found' });
      }

      // Prepare the response object
      const videoData = {
        _id: video._id,
        tags: video.tags,
        language: video.language,
        filename: video.filename,
        thumbnailUrl: video.thumbnailUrl,
        previewImageUrl: video.previewImageUrl,
        isMerged: video.isMerged,
        createdAt: video.createdAt,
      };

      if (video.isMerged) {
        videoData.mergedVideo = {
          platform: video.mergedVideo.platform,
          externalUrl: video.mergedVideo.externalUrl,
        };
      } else {
        videoData.uploadedVideo = {
          s3ObjectKey: video.uploadedVideo.s3ObjectKey,
          videoUrl: video.uploadedVideo.videoUrl,
          subtitles: video.uploadedVideo.subtitles,
          previewImageTimestamp: video.uploadedVideo.previewImageTimestamp,
          thumbnailStart: video.uploadedVideo.thumbnailStart,
          thumbnailEnd: video.uploadedVideo.thumbnailEnd,
        };
      }

      res.status(200).json(videoData);
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: 'Error retrieving video' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
};