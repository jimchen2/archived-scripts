import React, { useState, useEffect } from "react";
import axios from "axios";
import { Table, Button, Form, FormControl } from "react-bootstrap";
import ProjectForm from "./ProjectForm";
import ProjectTable from "./ProjectTable";
import { backendUrl } from "../../config";

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${backendUrl}/projects`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      setProjects(response.data);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
      setProjects([]);
      alert("Failed to fetch projects. Please try again.");
    }
  };

  const handleDeleteProject = async (projectId) => {
    try {
      await axios.delete(`${backendUrl}/projects/${projectId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      fetchProjects();
    } catch (error) {
      console.error("Failed to delete project:", error);
      alert(error);
    }
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const filteredProjects = projects.filter((project) =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <h2>Projects</h2>
      <ProjectForm onProjectCreated={fetchProjects} />

      <Form inline>
        <FormControl
          type="text"
          placeholder="Search by name"
          value={searchTerm}
          onChange={handleSearch}
        />
      </Form>
      <ProjectTable
        projects={filteredProjects}
        onDeleteProject={handleDeleteProject}
      />
    </div>
  );
};

export default Projects;
