// CourseForm.js
import React, { useState } from "react";
import axios from "axios";
import { Form, Button } from "react-bootstrap";
import { backendUrl } from "../../config";

const CourseForm = ({ onCourseCreated }) => {
  const [newCourse, setNewCourse] = useState({
    id: "",
    name: "",
    total_hours: "",
    level: "",
  });

  const handleCreateCourse = async () => {
    if (
      !newCourse.id ||
      !newCourse.name ||
      !newCourse.total_hours ||
      !newCourse.level
    ) {
      alert("请填写所有字段。 (Please fill in all the fields.)");
      return;
    }

    try {
      const response = await axios.post(
        `${backendUrl}/courses`,
        {
          ...newCourse,
          total_hours: parseInt(newCourse.total_hours),
          level: parseInt(newCourse.level),
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );
      if (response.status === 201) {
        onCourseCreated();
        setNewCourse({
          id: "",
          name: "",
          total_hours: "",
          level: "",
        });
      }
    } catch (error) {
      console.error("课程创建失败：", error);
      alert(
        "课程创建失败，请重试。 (Failed to create course. Please try again.)"
      );
    }
  };

  return (
    <div>
      <h3>添加课程 (Add Course)</h3>
      <Form>
        <Form.Group controlId="courseId">
          <Form.Label>ID</Form.Label>
          <Form.Control
            type="text"
            placeholder="输入课程 ID (Enter course ID)"
            value={newCourse.id}
            onChange={(e) => setNewCourse({ ...newCourse, id: e.target.value })}
            required
          />
        </Form.Group>
        <Form.Group controlId="courseName">
          <Form.Label>名称 (Name)</Form.Label>
          <Form.Control
            type="text"
            placeholder="输入课程名称 (Enter course name)"
            value={newCourse.name}
            onChange={(e) =>
              setNewCourse({ ...newCourse, name: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="courseTotalHours">
          <Form.Label>总时长 (Total Hours)</Form.Label>
          <Form.Control
            type="number"
            placeholder="输入总时长 (Enter total hours)"
            value={newCourse.total_hours}
            onChange={(e) =>
              setNewCourse({ ...newCourse, total_hours: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="courseLevel">
          <Form.Label>等级 (Level)</Form.Label>
          <Form.Control
            as="select"
            value={newCourse.level}
            onChange={(e) =>
              setNewCourse({ ...newCourse, level: e.target.value })
            }
            required
          >
            <option value="">选择课程等级 (Select course level)</option>
            <option value={1}>本科 (Undergraduate)</option>
            <option value={2}>研究生 (Graduate)</option>
          </Form.Control>
        </Form.Group>
        <Button variant="primary" onClick={handleCreateCourse}>
          创建课程 (Create Course)
        </Button>
      </Form>
    </div>
  );
};

export default CourseForm;
