import React from "react";
import { Row, Col, Image, Card } from "react-bootstrap";

const CommentCard = ({ index, comment }) => {
  const { data, mediaDetails, replyToContent, replyToAuthor } = comment;
  return (
    <div id={data["Reply Time"].slice(0, 20).replace(/\s/g, "_")}>
      <Row key={index} className="mb-3">
        <Col md={1}>
          <Image
            src={data["Face Image Source"]}
            alt={data["Face Image Alt"]}
            roundedCircle
            width={50}
            height={50}
          />
        </Col>
        <Col md={11}>
          <Card>
            <Card.Body>
              <Card.Title>
                <a
                  href={data["Douban Homepage"]}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <h6>{data["Face Image Alt"]}</h6>
                </a>
              </Card.Title>
              {replyToContent && (
                <>
                  <blockquote
                    className="blockquote mb-0"
                    style={{
                      marginTop: "20px",
                      backgroundColor: "#f9f9f9",
                      padding: "10px",
                      borderRadius: "5px",
                      fontSize: "16px",
                    }}
                  >
                    <p>{replyToContent}</p>
                    {replyToAuthor && (
                      <footer className="blockquote-footer">
                        {replyToAuthor}
                      </footer>
                    )}
                  </blockquote>{" "}
                  <br></br>
                </>
              )}
              <Card.Text>
                <p style={{ fontSize: "17px" }}>{data["Reply Content"]}</p>
              </Card.Text>
              {mediaDetails.map((media, idx) =>
                media.isImage ? (
                  <Image
                    key={idx}
                    src={media.localUrl}
                    alt="Media content"
                    fluid
                  />
                ) : (
                  <video
                    key={idx}
                    src={media.localUrl}
                    controls
                    style={{ width: "100%" }}
                  >
                    Your browser does not support video playback.
                  </video>
                )
              )}{" "}
              <p style={{ fontSize: "14px" }}> {data["Reply Time"]}</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default CommentCard;
