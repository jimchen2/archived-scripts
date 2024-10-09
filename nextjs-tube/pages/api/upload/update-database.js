import dbConnect from './mongoose';
import Video from '../models/Video';

export async function updateDatabase(
  s3ObjectKey,
  language,
  fileName,
  tags,
  previewImageTimestamp = 5,
  previewVideoStart = 0,
  previewVideoEnd = 15
) {
  await dbConnect();

  const video = new Video({
    tags,
    language,
    filename: fileName,
    isMerged: false,
    uploadedVideo: {
      s3ObjectKey,
      previewImageTimestamp,
      previewVideoStart,
      previewVideoEnd,
    },
  });

  await video.save();
  return video._id;
}