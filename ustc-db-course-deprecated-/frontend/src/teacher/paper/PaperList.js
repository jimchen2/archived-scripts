import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Table,
  Alert,
  Button,
  Spinner,
  FormControl,
  InputGroup,
} from "react-bootstrap";
import { Link } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import { backendUrl } from "../../config";

const TeacherPapers = () => {
  const [papers, setPapers] = useState([]);
  const [filteredPapers, setFilteredPapers] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchTeacherPapers();
  }, []);

  const fetchTeacherPapers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${backendUrl}/teacherpapers`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setPapers(response.data);
      setFilteredPapers(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching teacher papers:", error);
      setError("Failed to fetch teacher papers.");
      setLoading(false);
    }
  };

  const deletePaper = async (paperId) => {
    try {
      const token = localStorage.getItem("token");
      await axios.delete(`${backendUrl}/teacherpapers/${paperId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchTeacherPapers();
    } catch (error) {
      console.error("Error deleting paper:", error);
      setError("Failed to delete paper.");
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value.toLowerCase();
    setSearchQuery(query);
    setFilteredPapers(
      papers.filter((paper) => paper.name.toLowerCase().includes(query))
    );
  };

  return (
    <div className="mx-5 my-5">
      <h2 className="mb-4">My Papers</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      <InputGroup className="mb-4">
        <FormControl
          placeholder="Search Papers"
          value={searchQuery}
          onChange={handleSearchChange}
        />
      </InputGroup>
      {loading ? (
        <div className="text-center">
          <Spinner animation="border" role="status">
            <span className="sr-only">Loading...</span>
          </Spinner>
        </div>
      ) : (
        <Table striped bordered hover responsive className="shadow-sm w-100">
          <thead className="thead-dark">
            <tr>
              <th>Paper Name</th>
              <th>Source</th>
              <th>Year</th>
              <th>Type</th>
              <th>Level</th>
              <th>Ranking</th>
              <th>Corresponding Author</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredPapers.map((paper) => (
              <tr key={paper.id}>
                <td>{paper.name}</td>
                <td>{paper.source}</td>
                <td>{paper.year}</td>
                <td>{paper.type}</td>
                <td>{paper.level}</td>
                <td>{paper.ranking}</td>
                <td>{paper.is_corresponding_author ? "Yes" : "No"}</td>
                <td>
                  <Link to={`/paper/editpaper/${paper.id}`}>
                    <Button variant="primary" size="sm" className="mr-2 mb-1">
                      Edit
                    </Button>
                  </Link>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => deletePaper(paper.id)}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </div>
  );
};

export default TeacherPapers;
