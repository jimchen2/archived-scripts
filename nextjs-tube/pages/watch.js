import { useRouter } from "next/router";
import { useState, useEffect } from "react";

const Watch = () => {
  const router = useRouter();
  const { v: s3ObjectKey } = router.query;
  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (s3ObjectKey) {
      const fetchVideo = async () => {
        try {
          const response = await fetch(`/api/video?s3ObjectKey=${s3ObjectKey}`);
          const data = await response.json();

          if (response.ok) {
            setVideo(data);
          } else {
            setError(data.error);
          }
        } catch (err) {
          console.error("Error fetching video:", err);
          setError("Error fetching video");
        } finally {
          setLoading(false);
        }
      };

      fetchVideo();
    }
  }, [s3ObjectKey]);

  const handleDelete = async () => {
    try {
      const response = await fetch("/api/delete-file", {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fileName: s3ObjectKey }),
      });

      if (response.ok) {
        alert("File deleted successfully");
        router.push("/");
      } else {
        const data = await response.json();
        alert(`Failed to delete file: ${data.error}`);
      }
    } catch (err) {
      console.error("Error deleting file:", err);
      alert("Error deleting file");
    }
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <p>{error}</p>;

  return (
    <div className="container mx-auto mt-10 flex flex-col items-center">
      {video ? (
        <>
          <video
            controls
            className="max-w-[800px] w-[90%] mb-4"
            src={video.url}
          ></video>
          <br />
          <div className="w-[90%] max-w-[600px] shadow-lg p-4 hover:bg-gray-200 rounded-lg">
            <div className="flex justify-between items-center mb-2 font-semibold">
              <span className="text-md">{video.filename}</span>
              <button
                onClick={handleDelete}
                className="px-2 py-1 ring-1  rounded-lg text-gray-800 hover:bg-red-600 text-sm"
              >
                Delete
              </button>
            </div>
            <p className="text-gray-700 text-sm">
              Language: {video.language} | Tags: {video.tags.join(", ")}
            </p>
          </div>
        </>
      ) : (
        <p>Video not found</p>
      )}
    </div>
  );
};

export default Watch;
