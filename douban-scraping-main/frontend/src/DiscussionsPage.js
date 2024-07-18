import React, { useState, useEffect, useLayoutEffect } from "react";
import { Container, Card } from "react-bootstrap";
import { Link } from "react-router-dom";
import "./DiscussionsPage.css";
import BACKEND_URL from './config';

const DiscussionsPage = () => {
  const [discussions, setDiscussions] = useState([]);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // To update windowWidth when the window is resized
  useLayoutEffect(() => {
    const updateWindowWidth = () => {
        setWindowWidth(window.innerWidth);
    };

    window.addEventListener("resize", updateWindowWidth);
    
    updateWindowWidth();

    return () => window.removeEventListener("resize", updateWindowWidth);
  }, []);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/discussions`)
      .then((response) => response.json())
      .then((data) => setDiscussions(data))
      .catch((error) => console.error("获取数据时出错:", error));
  }, []);

  return (
    <Container>
      <br></br>

      <div className="discussion-list">
        {discussions.map((discussion) => (
          <Card key={discussion._id} className="discussion-card">
            <Card.Body>
              <Link
                to={`/${discussion["Topic ID"]}`}
                className="discussion-link"
              >
                <Card.Title>{discussion.Title}</Card.Title>
              </Link>
              <Card.Text className="d-md-flex justify-content-between text-truncate">
                <span>作者: {discussion.Author}</span>
                {windowWidth < 500 && <br />}
                <span>回复数: {discussion.Replies}</span>
                {windowWidth < 500 && <br />}
                <span>最后回帖: {discussion["Last Post Time"]}</span>
              </Card.Text>
              <div className="mt-2">
                <Link
                  to={`/${discussion["Topic ID"]}/comment?start=0`}
                  className="comment-link"
                >
                  查看评论
                </Link>
              </div>
            </Card.Body>
          </Card>
        ))}
      </div>
    </Container>
  );
};

export default DiscussionsPage;
