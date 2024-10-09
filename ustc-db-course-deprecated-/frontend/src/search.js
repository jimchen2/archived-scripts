import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Container, Row, Col, Form, Button, Card } from "react-bootstrap";
import { backendUrl } from "./config";

const SearchTeacher = () => {
  const [teacherId, setTeacherId] = useState("");
  const [startYear, setStartYear] = useState("");
  const [endYear, setEndYear] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.get(
        `${backendUrl}/search/${teacherId}/${startYear}-${endYear}`
      );
      setSearchResults(response.data);
    } catch (error) {
      console.error("Error searching for teacher:", error);
      alert("Failed to search for teacher. Please try again.");
    }
  };

  return (
    <Container>
      <Row>
        <Col>
          <h2>Search Teacher</h2>
          <Form onSubmit={handleSearch}>
            <Form.Group controlId="teacherId">
              <Form.Label>Teacher ID</Form.Label>
              <Form.Control
                type="text"
                value={teacherId}
                onChange={(e) => setTeacherId(e.target.value)}
                required
              />
            </Form.Group>
            <Form.Group controlId="startYear">
              <Form.Label>Start Year</Form.Label>
              <Form.Control
                type="number"
                value={startYear}
                onChange={(e) => setStartYear(e.target.value)}
                required
              />
            </Form.Group>
            <Form.Group controlId="endYear">
              <Form.Label>End Year</Form.Label>
              <Form.Control
                type="number"
                value={endYear}
                onChange={(e) => setEndYear(e.target.value)}
                required
              />
            </Form.Group>
            <Button variant="primary" type="submit">
              Search
            </Button>
          </Form>
        </Col>
      </Row>
      {searchResults && (
        <Row className="mt-4">
          <Col>
            <h3>Search Results</h3>
            <Card>
              <Card.Body>
                <Card.Title>{searchResults.teacher.name}</Card.Title>
                <Card.Text>
                  <strong>Teacher ID:</strong> {searchResults.teacher.id}
                </Card.Text>
                <Card.Text>
                  <strong>Papers:</strong>
                  <ul>
                    {searchResults.papers.map((paper, index) => (
                      <li key={index}>{paper.name}</li>
                    ))}
                  </ul>
                </Card.Text>
                <Card.Text>
                  <strong>Projects:</strong>
                  <ul>
                    {searchResults.projects.map((project, index) => (
                      <li key={index}>{project.name}</li>
                    ))}
                  </ul>
                </Card.Text>
                <Card.Text>
                  <strong>Courses:</strong>
                  <ul>
                    {searchResults.courses.map((course, index) => (
                      <li key={index}>{course.name}</li>
                    ))}
                  </ul>
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default SearchTeacher;
