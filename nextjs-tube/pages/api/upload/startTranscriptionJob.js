import { StartTranscriptionJobCommand } from "@aws-sdk/client-transcribe";
import { transcribeClient } from './transcribeClient';
import { getMediaFormat } from './mimeTypeMapping';

export async function startTranscriptionJob(s3ObjectKey, language, fileType) {
  const AWS_REGION = process.env.AWS_REGION;
  const S3_BUCKET_NAME = process.env.S3_BUCKET_NAME;
  
  const s3BucketUrl = AWS_REGION === 'us-east-1'
    ? `https://${S3_BUCKET_NAME}.s3.amazonaws.com`
    : `https://${S3_BUCKET_NAME}.s3-${AWS_REGION}.amazonaws.com`;

  const fileExtension = getMediaFormat(fileType);
  if (!fileExtension) {
    throw new Error('Unsupported file type');
  }

  const mediaUri = `${s3BucketUrl}/${s3ObjectKey}`;

  const params = {
    TranscriptionJobName: `${s3ObjectKey}_${language}`,
    LanguageCode: language,
    MediaFormat: fileExtension,
    Media: {
      MediaFileUri: mediaUri,
    },
    OutputBucketName: S3_BUCKET_NAME,
    Subtitles: {
      Formats: ["vtt"],
      OutputStartIndex: 1,
    },
  };

  const data = await transcribeClient.send(new StartTranscriptionJobCommand(params));
  return params.TranscriptionJobName;
}