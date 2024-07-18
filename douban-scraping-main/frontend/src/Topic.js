import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Card, Container, Row, Col, Image } from "react-bootstrap";
import Parser from "html-react-parser";
import BACKEND_URL from "./config";

const TopicDetail = () => {
  const { id } = useParams();
  const [topic, setTopic] = useState(null);
  const [discussion, setDiscussion] = useState(null);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/topics/${id}`)
      .then((response) => response.json())
      .then((data) => {
        const updatedContent = data["Main Content"].replace(
          /https?:\/\/img\d+\.doubanio\.com\/view\/group_topic\/l\/public\/(p\d+\.\w+)/g,
          `${BACKEND_URL}/media/$1`
        );

        data["Main Content"] = updatedContent;
        setTopic(data);
      });

    fetch(`${BACKEND_URL}/api/discussions`)
      .then((response) => response.json())
      .then((data) => {
        const foundDiscussion = data.find(
          (discussion) => discussion["Topic ID"] === id
        );
        setDiscussion(foundDiscussion);
      });
  }, [id]);

  return (
    <Container>
      {topic && discussion && (
        <Card className="my-4">
          <Card.Header>
            <Row noGutters>
              <Col xs={2} md={1}>
                <Image
                  src={topic["User Image Source"]}
                  alt={topic["User Image Alt Text"]}
                  roundedCircle
                  width="50px"
                  height="50px"
                />
              </Col>
              <Col xs={10} md={10}>
                <Card.Title className="mb-3">{discussion.Title}</Card.Title>

                <Card.Subtitle className="text-muted">
                  来自： {topic["User Image Alt Text"]}
                </Card.Subtitle>
              </Col>
            </Row>
          </Card.Header>
          <Card.Body>
            <Row>
              <Col xs={6}>
                <Link
                  to={`/${id}/comment?start=0`}
                  style={{ fontSize: "20px" }}
                >
                  查看评论
                </Link>
              </Col>
            </Row>
            <br />

            <Card.Text>{Parser(topic["Main Content"])}</Card.Text>
            <footer className="blockquote-footer">
              {new Date(topic["Post Time"]).toLocaleString("zh-CN", {
                timeZone: "Asia/Shanghai",
              })}
            </footer>
          </Card.Body>
        </Card>
      )}
    </Container>
  );
};

export default TopicDetail;
