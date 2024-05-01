// VideoCard.js

import React from "react";
import { Card } from "react-bootstrap";
import { Link } from "react-router-dom";
import VideoPlayer from "./VideoPlayer"; // Import the VideoPlayer component

function VideoCard({ video }) {
  if (!video) {
    console.error("VideoCard was given a null or undefined video object.");
    return null;
  }

  const decodedTitle = decodeURIComponent(video.title);
  const titleParts = decodedTitle.split("|||");
  const timestamp = titleParts?.[0];
  const userId = titleParts?.[1];
  const videoTitle = titleParts?.[2];

  const videourl = `https://cloudflare.jimchen.me/${timestamp}|||${userId}|||${encodeURIComponent(
    videoTitle
  )}`;

  const uploadedAtDate = timestamp
    ? new Date(parseInt(timestamp)).toLocaleString("default", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Date not available";

  return (
    <Card className="mb-4" style={{ maxWidth: '1000px', margin: 'auto' }}>
      <Card.Body>
        {video.id && (
            <VideoPlayer src={videourl} alt={`${videoTitle} video`} />
        )}
        <Card.Title className="mt-2">
          {video.id ? (
            <Link
              to={`/video/${video.id}`}
              className="text-primary"
              style={{ textDecoration: "none" }}
            >
              {videoTitle || "Untitled Video"}
            </Link>
          ) : (
            "Untitled Video"
          )}
        </Card.Title>
        <Card.Text>
          <br />
          Uploaded on: {uploadedAtDate}
        </Card.Text>
      </Card.Body>
    </Card>
  );
}

export default VideoCard;
