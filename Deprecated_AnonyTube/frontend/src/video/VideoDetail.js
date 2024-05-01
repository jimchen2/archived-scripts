import React, { useState, useEffect } from 'react';
import { Container } from 'react-bootstrap';
import { useParams } from 'react-router-dom';
import VideoCard from './SingleVideoCard.js'; // Make sure to import the VideoCard component
import { BACKEND_URL } from '../config.js';
function VideoDetail() {
  
  const { id } = useParams(); // Assuming 'id' is the video ID from the URL params
  const [video, setVideo] = useState(null);
  const [user, setUser] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initially, fetch all users and create a map by ID for easy access
    fetch(`${BACKEND_URL}/users`)
      .then(response => response.json())
      .then(usersData => {
        const usersById = usersData.reduce((acc, user) => {
          acc[user.id] = user;
          return acc;
        }, {});
        setUser(usersById);
      })
      .catch(error => console.error('Error fetching users:', error));

    // Fetch the complete list of videos
    fetch(`${BACKEND_URL}/videos`)
      .then(response => response.json())
      .then(videosData => {
        const foundVideo = videosData.find(v => v.id === id);
        if (foundVideo) {
          // Now that we have user details, attach them to the found video
          foundVideo.user = user[foundVideo.user_id];
          setVideo(foundVideo);
        } else {
          setVideo(null);
        }
      })
      .catch(videoError => {
        console.error('Error fetching videos:', videoError);
        setVideo(null);
      })
      .finally(() => {
        setLoading(false); // Indicates that loading has finished
      });
  }, [id]); // Depend on the ID and user object to re-run when they change

  if (loading) {
    return <Container>Loading...</Container>;
  }

  if (!video) {
    return <Container>No video found.</Container>;
  }

  // We now have the correct video, which we can pass to the VideoCard component
  return (
    <Container>
      <VideoCard video={video} />
    </Container>
  );
}

export default VideoDetail;
