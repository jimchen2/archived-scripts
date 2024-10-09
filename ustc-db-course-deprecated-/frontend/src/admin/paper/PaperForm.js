import React, { useState } from "react";
import axios from "axios";
import { Form, Button, Alert } from "react-bootstrap";
import { backendUrl } from "../../config";

const PaperForm = ({ onPaperAdded }) => {
  const [name, setName] = useState("");
  const [source, setSource] = useState("");
  const [year, setYear] = useState("");
  const [type, setType] = useState(1);
  const [level, setLevel] = useState(1);
  const [error, setError] = useState(null); // State for error message

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${backendUrl}/papers`,
        { name, source, year, type, level },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      onPaperAdded(); // Trigger the callback to refresh the paper list
      setName("");
      setSource("");
      setYear("");
      setType(1);
      setLevel(1);
      setError(null); // Clear any previous error message
    } catch (error) {
      console.error("Error adding paper:", error);
      // Set the error message from the backend
      if (error.response && error.response.data) {
        setError(`Error: ${error.response.data}`);
      } else {
        setError("An error occurred while adding the paper. Please try again.");
      }
    }
  };

  return (
    <div>
      <h2>添加论文 (Add Paper)</h2>
      {error && <Alert variant="danger">{error}</Alert>}{" "}
      {/* Conditionally render the error message */}
      <Form onSubmit={handleSubmit}>
        <Form.Group controlId="formName">
          <Form.Label>论文名称 (Name):</Form.Label>
          <Form.Control
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Form.Group>
        <Form.Group controlId="formSource">
          <Form.Label>发表源 (Source):</Form.Label>
          <Form.Control
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          />
        </Form.Group>
        <Form.Group controlId="formYear">
          <Form.Label>发表年份 (Year):</Form.Label>
          <Form.Control
            type="text"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          />
        </Form.Group>
        <Form.Group controlId="formType">
          <Form.Label>类型 (Type):</Form.Label>
          <Form.Control
            as="select"
            value={type}
            onChange={(e) => setType(parseInt(e.target.value))}
          >
            <option value={1}>全文论文 (Full Paper)</option>
            <option value={2}>短文论文 (Short Paper)</option>
            <option value={3}>海报论文 (Poster Paper)</option>
            <option value={4}>演示论文 (Demo Paper)</option>
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="formLevel">
          <Form.Label>级别 (Level):</Form.Label>
          <Form.Control
            as="select"
            value={level}
            onChange={(e) => setLevel(parseInt(e.target.value))}
          >
            <option value={1}>CCF-A</option>
            <option value={2}>CCF-B</option>
            <option value={3}>CCF-C</option>
            <option value={4}>中文CCF-A (Chinese CCF-A)</option>
            <option value={5}>中文CCF-B (Chinese CCF-B)</option>
            <option value={6}>无级别 (No Level)</option>
          </Form.Control>
        </Form.Group>
        <Button variant="primary" type="submit">
          添加 (Add Paper)
        </Button>
      </Form>
    </div>
  );
};

export default PaperForm;
