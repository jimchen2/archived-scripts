import React, { useState, useEffect } from "react";
import { Container } from "react-bootstrap";
import VideoPage from "./VideoPage"; // Ensure VideoPage is implemented with pagination
import { BACKEND_URL } from "../config";
function VideoList() {
  const [videos, setVideos] = useState([]);
  const [users, setUsers] = useState({});
  const [currentPage, setCurrentPage] = useState(1);
  const [pageCount, setPageCount] = useState(0);
  const itemsPerPage = 50; // Set the number of videos per page

  useEffect(() => {
    // Fetch all users
    fetch(`${BACKEND_URL}/users`)
      .then((response) => response.json())
      .then((usersData) => {
        // Transform users array into an object for easier access
        const usersById = usersData.reduce((acc, user) => {
          acc[user.id] = user;
          return acc;
        }, {});
        setUsers(usersById);
      })
      .catch((error) => console.error("Error fetching users:", error));

    // Fetch all videos
    fetch(`${BACKEND_URL}/videos`)
      .then((response) => response.json())
      .then((videosData) => {
        // Now that we have users, map each video to include user details
        const videosWithUser = videosData.map((video) => {
          return { ...video, user: users[video.user_id] };
        });

        setVideos(videosWithUser);
        setPageCount(Math.ceil(videosWithUser.length / itemsPerPage));
      })
      .catch((error) => console.error("Error fetching videos:", error));
  }, []); // Depend on users to re-run this effect when users are fetched

  // Calculate the videos to display on the current page
  const indexOfLastVideo = currentPage * itemsPerPage;
  const indexOfFirstVideo = indexOfLastVideo - itemsPerPage;
  const currentVideos = videos.slice(indexOfFirstVideo, indexOfLastVideo);

  return (
    <Container>
      <h2 className="my-4">Video List</h2>
      <VideoPage
        videos={currentVideos}
        itemsPerPage={itemsPerPage}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        pageCount={pageCount}
      />
    </Container>
  );
}

export default VideoList;
