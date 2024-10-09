import { useState } from "react";

export default function VideoCard({ video }) {
  const [isHovered, setIsHovered] = useState(false);
  console.log(video);

  return (
    <div className="border rounded-lg overflow-hidden shadow-lg">
      <div
        className="relative"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <img
          src={video.previewImageUrl}
          alt={video.filename}
          className="w-full h-auto object-cover transition-all duration-300"
        />
      </div>
      <div className="p-4">
        <h3 className="font-bold text-lg mb-2">{video.filename}</h3>
        <p className="text-gray-700 mb-2">Language: {video.language}</p>
        <p className="text-gray-700">Tags: {video.tags.join(", ")}</p>
      </div>
    </div>
  );
}
