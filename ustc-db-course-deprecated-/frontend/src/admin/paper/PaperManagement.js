import React, { useEffect, useState } from "react";
import axios from "axios";
import PaperForm from "./PaperForm";
import PaperTable from "./PaperTable";
import { backendUrl } from "../../config";

const PaperManagement = () => {
  const [papers, setPapers] = useState([]);

  useEffect(() => {
    fetchPapers();
  }, []);

  const fetchPapers = async () => {
    try {
      const response = await axios.get(`${backendUrl}/papers`);
      setPapers(response.data);
      console.log(response.data);
    } catch (error) {
      console.error("Failed to fetch papers:", error);
    }
  };

  const handlePaperAdded = () => {
    fetchPapers(); // Refresh the paper list
  };

  const handleDeletePaper = async (paperId) => {
    try {
      await axios.delete(`${backendUrl}/papers/${paperId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      setPapers(papers.filter((paper) => paper.paperId !== paperId));
    } catch (error) {
      console.error("Failed to delete paper:", error);
    }
  };

  return (
    <div>
      <h2>Paper Management</h2>
      <PaperForm onPaperAdded={handlePaperAdded} />
      <PaperTable papers={papers} onDeletePaper={handleDeletePaper} />
    </div>
  );
};

export default PaperManagement;
