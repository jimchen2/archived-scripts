import React from "react";
import { Table, Button } from "react-bootstrap";


const CourseTable = ({ courses, onDeleteCourse }) => {
  return (
    <Table striped bordered hover>
      <thead>
        <tr>
          <th>ID</th>
          <th>名称 (Name)</th>
          <th>总时长 (Total Hours)</th>
          <th>等级 (Level)</th>
          <th>操作 (Actions)</th>
        </tr>
      </thead>
      <tbody>
        {courses.map((course) => (
          <tr key={course.id}>
            <td>{course.id}</td>
            <td>{course.name}</td>
            <td>{course.total_hours}</td>
            <td>{course.level === 1 ? "本科 (Undergraduate)" : "研究生 (Graduate)"}</td>
            <td>
              <Button
                variant="danger"
                onClick={() => onDeleteCourse(course.id)}
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

export default CourseTable;
