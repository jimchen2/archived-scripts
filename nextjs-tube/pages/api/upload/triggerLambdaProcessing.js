import { LambdaClient, InvokeCommand } from '@aws-sdk/client-lambda';

const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION });

export async function triggerLambdaProcessing(
  url,
  s3ObjectKey,
  previewImageTimestamp,
  previewVideoStart,
  previewVideoEnd
) {
  const params = {
    FunctionName: process.env.FunctionName,
    InvocationType: 'Event',
    Payload: JSON.stringify({
      password: process.env.LAMBDA_PASSWORD,
      url,
      s3ObjectKey,
      previewImageTimestamp,
      previewVideoStart,
      previewVideoEnd,
      bucket: process.env.S3_BUCKET_NAME
    }),
  };

  const command = new InvokeCommand(params);
  await lambdaClient.send(command);
}