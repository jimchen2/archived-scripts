import React, { useState } from "react";
import axios from "axios";
import { Button, Alert } from "react-bootstrap";
import { backendUrl } from "../../config";

const TeacherExport = () => {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    try {
      const response = await axios.get(`${backendUrl}/teacherexport/report`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`, // Assumes token is stored in localStorage
        },
      });
      setReport(response.data);
      setError(null);
    } catch (err) {
      setReport(null);
      setError("Error generating report");
    }
  };

  return (
    <div>
      <h2>Teacher Export</h2>
      <Button onClick={handleExport}>Export</Button>

      {error && <Alert variant="danger">{error}</Alert>}

      {report && <pre>{JSON.stringify(report, null, 2)}</pre>}
      <br />
      <br />
      <br />
      <br />
    </div>
  );
};

export default TeacherExport;
