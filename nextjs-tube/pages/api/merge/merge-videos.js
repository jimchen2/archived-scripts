import dbConnect from "../../../lib/mongoose";
import Video from "../../../models/Video";

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ message: "Method not allowed" });
  }

  try {
    await dbConnect();

    const body = await parseFormData(req);

    // Check if filename is provided
    if (!body.filename) {
      return res.status(400).json({ message: "Filename is required" });
    }

    // Extract video ID from URL
    const videoId = extractYouTubeVideoId(body.externalUrl);
    if (!videoId) {
      return res.status(400).json({ message: "Invalid YouTube URL" });
    }

    // Generate previewVideo and preview image URLs
    const previewVideoUrl = `https://img.youtube.com/vi/${videoId}/default.jpg`;
    const previewImageUrl = `https://img.youtube.com/vi/${videoId}/0.jpg`;

    // Parse tags
    const tags = JSON.parse(body.tags || "[]");

    // Extract the first part of the language code (e.g., "en" from "en-US")
    const language = body.language.split("-")[0];

    // Create new Video document
    const newVideo = new Video({
      tags,
      language,
      filename: body.filename,
      previewVideoUrl,
      previewImageUrl,
      isMerged: true,
      mergedVideo: {
        platform: body.platform,
        externalUrl: body.externalUrl,
      },
    });

    // Save to MongoDB
    await newVideo.save();

    res
      .status(201)
      .json({ message: "Video merged successfully", video: newVideo });
  } catch (error) {
    console.error("Error merging video:", error);
    res
      .status(500)
      .json({ message: "Error merging video", error: error.message });
  }
}

function parseFormData(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      const fields = {};
      body.split("\r\n").forEach((line, index, array) => {
        if (line.includes("Content-Disposition: form-data; name=")) {
          const name = line.match(/name="([^"]+)"/)[1];
          fields[name] = array[index + 2];
        }
      });
      resolve(fields);
    });
  });
}

function extractYouTubeVideoId(url) {
  if (!url) return null;

  const regExp =
    /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
  const match = url.match(regExp);

  if (match && match[2].length === 11) {
    return match[2];
  } else {
    // Handle youtu.be URLs
    const shortUrlRegExp = /^(https?:\/\/)?youtu\.be\/([^#\&\?]*).*/;
    const shortUrlMatch = url.match(shortUrlRegExp);
    if (shortUrlMatch && shortUrlMatch[2].length === 11) {
      return shortUrlMatch[2];
    }
  }

  return null;
}
