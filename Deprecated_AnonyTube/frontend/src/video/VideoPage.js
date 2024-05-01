import React, { useState } from 'react';
import { Container, Row, Col, Pagination } from 'react-bootstrap';
import VideoCard from './VideoCard';

function VideoPage({ videos = [], itemsPerPage = 50 }) { // Default videos to an empty array
  const [currentPage, setCurrentPage] = useState(1);
  const pageCount = Math.ceil(videos.length / itemsPerPage);

  // Set up page numbers for pagination.
  const pageNumbers = [];
  for (let i = 1; i <= pageCount; i++) {
    pageNumbers.push(i);
  }

  // Calculate the current video items.
  const indexOfLastVideo = currentPage * itemsPerPage;
  const indexOfFirstVideo = indexOfLastVideo - itemsPerPage;
  const currentVideos = videos.slice(indexOfFirstVideo, indexOfLastVideo);

  return (
    <Container>
      <Row>
        {currentVideos.map((video, index) => (
          <Col md={4} key={index}> {/* Changed key to index for simplicity */}
            <VideoCard video={video} />
          </Col>
        ))}
      </Row>
      {pageCount > 1 && (
        <Pagination className="justify-content-center my-4">
          <Pagination.First onClick={() => setCurrentPage(1)} disabled={currentPage === 1} />
          <Pagination.Prev onClick={() => setCurrentPage(currentPage - 1)} disabled={currentPage === 1} />
          {pageNumbers.map(number => (
            <Pagination.Item key={number} active={number === currentPage} onClick={() => setCurrentPage(number)}>
              {number}
            </Pagination.Item>
          ))}
          <Pagination.Next onClick={() => setCurrentPage(currentPage + 1)} disabled={currentPage === pageCount} />
          <Pagination.Last onClick={() => setCurrentPage(pageCount)} disabled={currentPage === pageCount} />
        </Pagination>
      )}
    </Container>
  );
}

export default VideoPage;
