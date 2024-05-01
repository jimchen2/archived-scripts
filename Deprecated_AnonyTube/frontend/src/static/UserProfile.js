import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import VideoPage from "../video/VideoPage";
import { BACKEND_URL } from '../config';
const UserProfile = () => {
  const [videos, setVideos] = useState([]);
  const [username, setUsername] = useState(''); // Assuming you'll store the username here
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageCount, setPageCount] = useState(0);
  const itemsPerPage = 10; // Or any other number you prefer

  // Extract the userID from the URL
  const { userID } = useParams();

  useEffect(() => {
    setLoading(true);
    const fetchUsers = fetch(`${BACKEND_URL}/users`).then(res => res.json());
    const fetchVideos = fetch(`${BACKEND_URL}/videos`).then(res => res.json());

    Promise.all([fetchUsers, fetchVideos])
      .then(([users, videos]) => {
        const user = users.find(user => user.id === userID);
        if (user) {
          setUsername(user.username); // Set the username for use in the component
        }

        const userVideos = videos
          .filter(video => video.user_id === userID)
          .map(video => ({
            ...video,
            username: user.username, // Assuming you want to include this for each video
          }));

        setVideos(userVideos);
        setPageCount(Math.ceil(userVideos.length / itemsPerPage));
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setError(error);
      })
      .finally(() => setLoading(false));
  }, [userID]);

  const indexOfLastVideo = currentPage * itemsPerPage;
  const indexOfFirstVideo = indexOfLastVideo - itemsPerPage;
  const currentVideos = videos.slice(indexOfFirstVideo, indexOfLastVideo);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
    <div style={{ textAlign: 'center' }}>
      {username && <h2>{username}'s Videos</h2>}
    </div>
      
      <VideoPage
        videos={currentVideos}
        itemsPerPage={itemsPerPage}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        pageCount={pageCount}
      />
    </div>
  );
};

export default UserProfile;
