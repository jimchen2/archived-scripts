// pages/api/projects/upload.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { v4 as uuidv4 } from 'uuid';
import formidable, { File as FormidableFile, Fields, Files } from 'formidable'; // Import File as FormidableFile
import fs from 'fs'; // Node.js file system module

// Ensure environment variables are asserted as strings or handled if undefined
const r2Endpoint = process.env.R2_ENDPOINT;
const r2AccessKeyId = process.env.R2_ACCESS_KEY_ID;
const r2SecretAccessKey = process.env.R2_SECRET_ACCESS_KEY;
const r2BucketName = process.env.R2_BUCKET_NAME;
const r2PublicUrlPrefix = process.env.R2_PUBLIC_URL_PREFIX;

if (!r2Endpoint || !r2AccessKeyId || !r2SecretAccessKey || !r2BucketName || !r2PublicUrlPrefix) {
  console.error("Missing R2 configuration in environment variables.");
}

// though the handler will fail if s3Client is not properly initialized.
let s3Client: S3Client | null = null;
if (r2Endpoint && r2AccessKeyId && r2SecretAccessKey) {
  s3Client = new S3Client({
    region: "auto",
    endpoint: r2Endpoint,
    credentials: {
      accessKeyId: r2AccessKeyId,
      secretAccessKey: r2SecretAccessKey,
    },
  });
}

// IMPORTANT: Disable Next.js's default body parser for this route to handle multipart/form-data
export const config = {
  api: {
    bodyParser: false,
  },
};

// Define a type for the expected JSON response
type Data = {
  fileUrl?: string;
  error?: string;
  details?: string;
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<Data>
) {
  if (!s3Client || !r2BucketName || !r2PublicUrlPrefix) {
    console.error("R2 S3 client or bucket configuration is missing.");
    return res.status(500).json({ error: "Server configuration error for file uploads." });
  }

  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
  }

  const form = formidable({}); // Initialize formidable
  let tempFilePath: string | null = null; // To store path for cleanup

  try {
    const [fields, files]: [Fields, Files] = await form.parse(req);

    const fileData = files.file; // 'file' should match FormData key

    if (!fileData) {
      return res.status(400).json({ error: "No file found in the form data." });
    }

    // formidable might return a single file or an array of files.
    // Since client sends one file, we expect a single FormidableFile or an array with one.
    let actualFile: FormidableFile;
    if (Array.isArray(fileData)) {
      if (fileData.length === 0) {
        return res.status(400).json({ error: "No file uploaded (empty array received)." });
      }
      actualFile = fileData[0];
    } else {
      actualFile = fileData;
    }

    tempFilePath = actualFile.filepath; // Store for cleanup

    if (!actualFile.originalFilename) {
      return res.status(400).json({ error: "Uploaded file is missing an original name." });
    }
    const fileExtension = actualFile.originalFilename.split(".").pop();
    if (!fileExtension) {
      return res.status(400).json({ error: "Could not determine file extension from original name." });
    }

    if (!actualFile.mimetype) {
      return res.status(400).json({ error: "Could not determine file MIME type." });
    }
    const contentType = actualFile.mimetype;

    const buffer = fs.readFileSync(actualFile.filepath);
    const uniqueFileName = `${uuidv4()}.${fileExtension}`;
    const fileKey = `project-files/${uniqueFileName}`;

    const params = {
      Bucket: r2BucketName,
      Key: fileKey,
      Body: buffer,
      ContentType: contentType,
    };

    const command = new PutObjectCommand(params);
    await s3Client.send(command);

    const fileUrl = `${r2PublicUrlPrefix}/${fileKey}`;

    // Clean up the temporary file
    fs.unlinkSync(actualFile.filepath);
    tempFilePath = null; // Mark as cleaned up

    return res.status(200).json({ fileUrl });

  } catch (error: any) {
    console.error("Error in /api/projects/upload:", error);

    // Attempt to clean up temp file if it still exists
    if (tempFilePath && fs.existsSync(tempFilePath)) {
      try {
        fs.unlinkSync(tempFilePath);
      } catch (unlinkError) {
        console.error("Error cleaning up temp file on error:", unlinkError);
      }
    }
    return res.status(500).json({ error: "Failed to upload file to storage.", details: error.message });
  }
}