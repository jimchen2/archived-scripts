import { S3Client, DeleteObjectCommand } from '@aws-sdk/client-s3';
import dbConnect from '../../lib/mongoose';
import Video from '../../models/Video';

const region = process.env.AWS_REGION;
const accessKeyId = process.env.AWS_ACCESS_KEY_ID;
const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY;
const bucketName = process.env.S3_BUCKET_NAME;
const adminPassword = process.env.ADMIN_PASSWORD;

const s3Client = new S3Client({
  region,
  credentials: {
    accessKeyId,
    secretAccessKey,
  },
});

export default async (req, res) => {
  await dbConnect();

  if (req.method === 'DELETE') {
    const { videoId } = req.body;
    const { adminAuth } = req.cookies;

    // Check admin password from cookie
    if (adminAuth !== adminPassword) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    try {
      // Find the video in the database
      const video = await Video.findById(videoId);
      if (!video) {
        return res.status(404).json({ error: 'Video not found' });
      }

      // If it's not a merged video, delete from S3
      if (!video.isMerged) {
        // Delete video file
        if (video.uploadedVideo.s3ObjectKey) {
          const videoParams = {
            Bucket: bucketName,
            Key: video.uploadedVideo.s3ObjectKey,
          };
          await s3Client.send(new DeleteObjectCommand(videoParams));
        }

        // Delete subtitle files
        for (const subtitle of video.uploadedVideo.subtitles) {
          const subtitleParams = {
            Bucket: bucketName,
            Key: subtitle.url.split('/').pop(), // Assuming the key is the last part of the URL
          };
          await s3Client.send(new DeleteObjectCommand(subtitleParams));
        }
      }

      // Delete thumbnail and preview image
      if (video.thumbnailUrl) {
        const thumbnailParams = {
          Bucket: bucketName,
          Key: video.thumbnailUrl.split('/').pop(),
        };
        await s3Client.send(new DeleteObjectCommand(thumbnailParams));
      }

      if (video.previewImageUrl) {
        const previewParams = {
          Bucket: bucketName,
          Key: video.previewImageUrl.split('/').pop(),
        };
        await s3Client.send(new DeleteObjectCommand(previewParams));
      }

      // Delete the video from the database
      await Video.findByIdAndDelete(videoId);

      res.status(200).json({ message: 'Video deleted successfully' });
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: 'Error deleting video' });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
};