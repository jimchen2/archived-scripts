import React, { useState, useEffect } from "react";
import axios from "axios";
import PaperForm from "./PaperForm";
import { Alert } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import { backendUrl } from "../../config";

const AddPaper = () => {
  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState("");
  const [ranking, setRanking] = useState("");
  const [isCorrespondingAuthor, setIsCorrespondingAuthor] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchPapers();
  }, []);

  const fetchPapers = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${backendUrl}/papers`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setPapers(response.data);
    } catch (error) {
      console.error("Error fetching papers:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `${backendUrl}/teacherpapers`,
        {
          paper_id: selectedPaper,
          ranking: parseInt(ranking),
          is_corresponding_author: isCorrespondingAuthor,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setSelectedPaper("");
      setRanking("");
      setIsCorrespondingAuthor(false);
      setError("");
      setSuccess("Paper added successfully!");
    } catch (error) {
      setError(error.response.data);
      setSuccess("");
      console.error("Error adding paper:", error);
    }
  };

  return (
    <div className="container">
      <h2>Add Paper</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      <PaperForm
        papers={papers}
        selectedPaper={selectedPaper}
        setSelectedPaper={setSelectedPaper}
        ranking={ranking}
        setRanking={setRanking}
        isCorrespondingAuthor={isCorrespondingAuthor}
        setIsCorrespondingAuthor={setIsCorrespondingAuthor}
        handleSubmit={handleSubmit}
      />
    </div>
  );
};

export default AddPaper;
