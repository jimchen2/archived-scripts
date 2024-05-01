import React from "react";
import { Card } from "react-bootstrap";
import { Link } from "react-router-dom";

function VideoCard({ video }) {
  if (!video) {
    console.error("VideoCard was given a null or undefined video object.");
    return null;
  }

  // Decode the URL-encoded title from the server
  const decodedTitle = decodeURIComponent(video.title);

  // Extract DATE, UserId, and VideoTitle from the decoded title
  const titleParts = decodedTitle.split("|||");
  const timestamp = titleParts?.[0];
  const userId = titleParts?.[1];
  const videoTitle = titleParts?.[2];

  // Compute the preview image URL using the title with the '.png' extension
  const previewImageUrl = `https://cloudflare.jimchen.me/${timestamp}|||${userId}|||${encodeURIComponent(
    videoTitle
  )}.png`;

  // Format the date, default to not available if timestamp is undefined
  const uploadedAtDate = timestamp
    ? new Date(parseInt(timestamp)).toLocaleString("default", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Date not available";

  // Get the username or set a default
  const username = video.user?.username ?? "Unknown User";

  return (
    <Card className="mb-4">
      <Card.Body>
        {video.id && (
          <Link to={`/video/${video.id}`}>
            <Card.Img
              variant="top"
              src={previewImageUrl}
              alt={`${videoTitle} Preview`}
            />
          </Link>
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
          Uploaded by:{" "}
          {userId ? <Link to={`/user/${userId}`}>{username}</Link> : username}
          <br />
          Uploaded on: {uploadedAtDate}
        </Card.Text>
      </Card.Body>
    </Card>
  );
}

export default VideoCard;
