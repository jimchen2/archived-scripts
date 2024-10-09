import React from "react";
import { Table, Button } from "react-bootstrap";

const ProjectTable = ({ projects, onDeleteProject }) => {
  return (
    <Table striped bordered hover>
      <thead>
        <tr>
          <th>ID</th>
          <th>名称 (Name)</th>
          <th>来源 (Source)</th>
          <th>项目类型 (Project Type)</th>
          <th>总资金 (Total Funding)</th>
          <th>开始年份 (Start Year)</th>
          <th>结束年份 (End Year)</th>
          <th>操作 (Actions)</th>
        </tr>
      </thead>
      <tbody>
        {projects.map((project) => (
          <tr key={project.id}>
            <td>{project.id}</td>
            <td>{project.name}</td>
            <td>{project.source}</td>
            <td>
              {project.project_type === 1
                ? "国家级项目 (Type 1)"
                : project.project_type === 2
                ? "省部级项目 (Type 2)"
                : project.project_type === 3
                ? "市厅级项目 (Type 3)"
                : project.project_type === 4
                ? "企业合作项目 (Type 4)"
                : project.project_type === 5
                ? "其它类型项目 (Type 5)"
                : ""}
            </td>
            <td>{project.total_funding}</td>
            <td>{project.start_year}</td>
            <td>{project.end_year}</td>
            <td>
              <Button
                variant="danger"
                onClick={() => onDeleteProject(project.id)}
              >
                删除 (Delete)
              </Button>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

export default ProjectTable;
