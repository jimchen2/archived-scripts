import { TranscribeClient } from "@aws-sdk/client-transcribe";

const REGION = process.env.AWS_REGION; 

const transcribeClient = new TranscribeClient({ region: REGION });

export { transcribeClient };
