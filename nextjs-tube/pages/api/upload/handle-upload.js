// pages/api/handle-upload.js

import { generatePresignedUrl } from './generate-presigned-url';
import { startTranscriptionJob } from './startTranscriptionJob';
import { triggerLambdaProcessing } from './triggerLambdaProcessing';
import Video from '../models/Video';

export default async function handleUpload(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { 
      fileName, 
      fileType, 
      language, 
      tags, 
      previewImageTimestamp = 5, 
      previewVideoStart = 0, 
      previewVideoEnd = 10 
    } = req.body;

    // Step 1: Generate presigned URL
    const { url, s3ObjectKey } = await generatePresignedUrl(fileName, fileType);
    
    // Step 2: Start transcription job
    const transcriptionJobName = await startTranscriptionJob(s3ObjectKey, language, fileType);

    // Step 3: Trigger Lambda for preview image and previewVideo extraction
    const lambdaPromise = triggerLambdaProcessing(
      url,
      s3ObjectKey,
      previewImageTimestamp.toString(),
      previewVideoStart.toString(),
      previewVideoEnd.toString()
    );

    // Construct URLs
    const s3PublicUrl = process.env.S3_PUBLIC_URL;
    const previewVideoUrl = `${s3PublicUrl}/${s3ObjectKey}_previewVideo.gif`;
    const previewImageUrl = `${s3PublicUrl}/${s3ObjectKey}_preview.jpg`;
    const subtitleUrl = `${s3PublicUrl}/${s3ObjectKey}.vtt`;

    // Step 4: Create new Video document in the database
    const video = new Video({
      tags,
      language,
      filename: fileName,
      previewVideoUrl,
      previewImageUrl,
      isMerged: false,
      uploadedVideo: {
        s3ObjectKey,
        videoUrl: url,
        subtitles: [{ language, url: subtitleUrl }],
        previewImageTimestamp,
        previewVideoStart,
        previewVideoEnd,
      }
    });

    await video.save();
    
    // Return all necessary information to the client
    res.status(200).json({
      url,
      s3ObjectKey,
      videoId: video._id,
      transcriptionJobName,
      subtitleUrl,
      message: 'Upload process initiated successfully',
    });
  } catch (error) {
    console.error('Error in handleUpload:', error);
    res.status(500).json({ error: 'Failed to process upload', details: error.message });
  }
}