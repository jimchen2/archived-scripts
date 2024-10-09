import React, { useState } from "react";
import axios from "axios";
import { Form, Button, Alert } from "react-bootstrap";
import { backendUrl } from "../../config";

const ProjectForm = ({ onProjectCreated }) => {
  const [newProject, setNewProject] = useState({
    id: "",
    name: "",
    source: "",
    project_type: "",
    total_funding: "",
    start_year: "",
    end_year: "",
  });

  const [error, setError] = useState(null);

  const handleCreateProject = async () => {
    if (
      !newProject.id ||
      !newProject.name ||
      !newProject.source ||
      !newProject.project_type ||
      !newProject.total_funding ||
      !newProject.start_year ||
      !newProject.end_year
    ) {
      setError("请填写所有字段。 (Please fill in all the fields.)");
      return;
    }

    try {
      const response = await axios.post(
        `${backendUrl}/projects`,
        {
          ...newProject,
          project_type: parseInt(newProject.project_type),
          total_funding: parseFloat(newProject.total_funding),
          start_year: parseInt(newProject.start_year),
          end_year: parseInt(newProject.end_year),
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      if (response.status === 201) {
        onProjectCreated();
        setNewProject({
          id: "",
          name: "",
          source: "",
          project_type: "",
          total_funding: "",
          start_year: "",
          end_year: "",
        });
        setError(null);
      }
    } catch (error) {
      console.error("创建项目失败：", error);
      setError(
        "创建项目失败，请重试。 (Failed to create project. Please try again.)"
      );
    }
  };

  return (
    <div>
      <h3>添加项目 (Add Project)</h3>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form>
        <Form.Group controlId="projectId">
          <Form.Label>ID</Form.Label>
          <Form.Control
            type="text"
            placeholder="输入项目 ID (Enter project ID)"
            value={newProject.id}
            onChange={(e) =>
              setNewProject({ ...newProject, id: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="projectName">
          <Form.Label>名称 (Name)</Form.Label>
          <Form.Control
            type="text"
            placeholder="输入项目名称 (Enter project name)"
            value={newProject.name}
            onChange={(e) =>
              setNewProject({ ...newProject, name: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="projectSource">
          <Form.Label>来源 (Source)</Form.Label>
          <Form.Control
            type="text"
            placeholder="输入项目来源 (Enter project source)"
            value={newProject.source}
            onChange={(e) =>
              setNewProject({ ...newProject, source: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="projectType">
          <Form.Label>项目类型 (Project Type)</Form.Label>
          <Form.Control
            as="select"
            value={newProject.project_type}
            onChange={(e) =>
              setNewProject({ ...newProject, project_type: e.target.value })
            }
            required
          >
            <option value="">选择项目类型 (Select project type)</option>
            <option value="1">国家级项目 (Type 1)</option>
            <option value="2">省部级项目 (Type 2)</option>
            <option value="3">市厅级项目 (Type 3)</option>
            <option value="4">企业合作项目 (Type 4)</option>
            <option value="5">其它类型项目 (Type 5)</option>
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="projectFunding">
          <Form.Label>总资金 (Total Funding)</Form.Label>
          <Form.Control
            type="number"
            placeholder="输入总资金 (Enter total funding)"
            value={newProject.total_funding}
            onChange={(e) =>
              setNewProject({ ...newProject, total_funding: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="projectStartYear">
          <Form.Label>开始年份 (Start Year)</Form.Label>
          <Form.Control
            type="number"
            placeholder="输入开始年份 (Enter start year)"
            value={newProject.start_year}
            onChange={(e) =>
              setNewProject({ ...newProject, start_year: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="projectEndYear">
          <Form.Label>结束年份 (End Year)</Form.Label>
          <Form.Control
            type="number"
            placeholder="输入结束年份 (Enter end year)"
            value={newProject.end_year}
            onChange={(e) =>
              setNewProject({ ...newProject, end_year: e.target.value })
            }
            required
          />
        </Form.Group>
        <Button variant="primary" onClick={handleCreateProject}>
          创建项目 (Create Project)
        </Button>
      </Form>
    </div>
  );
};

export default ProjectForm;
