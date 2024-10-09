import VideoCard from "./VideoCard";

export default function VideoGrid({ videos }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {videos && videos.length > 0 ? (
        videos.map((video) => (
          <VideoCard key={video._id} video={video} />
        ))
      ) : (
        <div className="col-span-full text-center py-10">
          <p className="text-gray-500 text-lg">No videos available.</p>
        </div>
      )}
    </div>
  );
}