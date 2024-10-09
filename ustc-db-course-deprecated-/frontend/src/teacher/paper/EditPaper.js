import React, { useState, useEffect } from "react";
import axios from "axios";
import { Form, Button, Alert } from "react-bootstrap";
import { useParams, useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import { backendUrl } from "../../config";

const EditPaper = () => {
  const [paper, setPaper] = useState({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const { paperId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    fetchPaper();
  }, []);

  const fetchPaper = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(
        `${backendUrl}/teacherpapers/${paperId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setPaper(response.data);
    } catch (error) {
      console.error("Error fetching paper:", error);
      setError("Failed to fetch paper.");
    }
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      await axios.put(
        `${backendUrl}/teacherpapers/${paperId}`,
        {
          ranking: paper.ranking,
          is_corresponding_author: paper.is_corresponding_author,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setSuccess("Paper updated successfully!");
      setTimeout(() => {
        navigate("/teacherpapers");
      }, 2000);
    } catch (error) {
      console.error("Error updating paper:", error);
      setError("Failed to update paper.");
    }
  };

  return (
    <div className="container">
      <h2>Edit Paper</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      <Form onSubmit={handleSubmit}>
        <Form.Group controlId="name">
          <Form.Label>Paper Name</Form.Label>
          <Form.Control
            type="text"
            name="name"
            value={paper.name || ""}
            disabled
          />
        </Form.Group>

        <Form.Group controlId="source">
          <Form.Label>Source</Form.Label>
          <Form.Control
            type="text"
            name="source"
            value={paper.source || ""}
            disabled
          />
        </Form.Group>

        <Form.Group controlId="year">
          <Form.Label>Year</Form.Label>
          <Form.Control
            type="number"
            name="year"
            value={paper.year || ""}
            disabled
          />
        </Form.Group>

        <Form.Group controlId="type">
          <Form.Label>Type</Form.Label>
          <Form.Control
            type="text"
            name="type"
            value={paper.type || ""}
            disabled
          />
        </Form.Group>

        <Form.Group controlId="level">
          <Form.Label>Level</Form.Label>
          <Form.Control
            type="text"
            name="level"
            value={paper.level || ""}
            disabled
          />
        </Form.Group>

        <Form.Group controlId="ranking">
          <Form.Label>Ranking</Form.Label>
          <Form.Control
            type="number"
            name="ranking"
            value={paper.ranking || ""}
            onChange={(e) => setPaper({ ...paper, ranking: e.target.value })}
            required
          />
        </Form.Group>

        <Form.Group controlId="isCorrespondingAuthor">
          <Form.Check
            type="checkbox"
            label="Corresponding Author"
            name="is_corresponding_author"
            checked={paper.is_corresponding_author || false}
            onChange={(e) =>
              setPaper({ ...paper, is_corresponding_author: e.target.checked })
            }
          />
        </Form.Group>

        <Button variant="primary" type="submit">
          Update Paper
        </Button>
      </Form>
    </div>
  );
};

export default EditPaper;
