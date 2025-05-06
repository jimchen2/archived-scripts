import React, { useState } from "react";
import axios from "axios";
import { Form, Button } from "react-bootstrap";
import { backendUrl } from "../../config";

const TeacherForm = ({ onTeacherCreated }) => {
  const [newTeacher, setNewTeacher] = useState({
    id: "",
    name: "",
    gender: "",
    title: "",
    password: "",
  });

  const handleCreateTeacher = async () => {
    if (
      !newTeacher.id ||
      !newTeacher.name ||
      !newTeacher.gender ||
      !newTeacher.title ||
      !newTeacher.password
    ) {
      alert("请填写所有字段。");
      return;
    }

    try {
      const response = await axios.post(`${backendUrl}/teachers`, newTeacher, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (response.status === 201) {
        onTeacherCreated();
        setNewTeacher({
          id: "",
          name: "",
          gender: "",
          title: "",
          password: "",
        });
      }
    } catch (error) {
      console.error("创建教师失败:", error);
      alert("创建教师失败，请重试，检查是否重复创建。");
    }
  };

  return (
    <div>
      <h3>添加教师</h3>
      <Form>
        <Form.Group controlId="teacherId">
          <Form.Label>工号 (ID)</Form.Label>
          <Form.Control
            type="text"
            placeholder="请输入教师工号（5位字符）"
            value={newTeacher.id}
            onChange={(e) =>
              setNewTeacher({ ...newTeacher, id: e.target.value })
            }
            maxLength="5"
            required
          />
        </Form.Group>
        <Form.Group controlId="teacherName">
          <Form.Label>姓名</Form.Label>
          <Form.Control
            type="text"
            placeholder="请输入教师姓名"
            value={newTeacher.name}
            onChange={(e) =>
              setNewTeacher({ ...newTeacher, name: e.target.value })
            }
            required
          />
        </Form.Group>
        <Form.Group controlId="teacherGender">
          <Form.Label>性别 (Gender)</Form.Label>
          <Form.Control
            as="select"
            value={newTeacher.gender}
            onChange={(e) =>
              setNewTeacher({ ...newTeacher, gender: e.target.value })
            }
            required
          >
            <option value="">选择性别</option>
            <option value="1">男性 (Male)</option>
            <option value="2">女性 (Female)</option>
            <option value="3">双性 (Intersex)</option>
            <option value="4">非二元性别 (Non-binary)</option>
            <option value="5">性别酷儿 (Genderqueer)</option>
            <option value="6">性别流动 (Genderfluid)</option>
            <option value="7">无性别 (Agender)</option>
            <option value="8">双性别 (Bigender)</option>
            <option value="9">性别多样 (Gender diverse)</option>
            <option value="10">双魂 (Two-Spirit)</option>
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="teacherTitle">
          <Form.Label>职称 (Title)</Form.Label>
          <Form.Control
            as="select"
            value={newTeacher.title}
            onChange={(e) =>
              setNewTeacher({ ...newTeacher, title: e.target.value })
            }
            required
          >
            <option value="">选择职称</option>
            <option value="1">博士后 (Postdoctoral)</option>
            <option value="2">助教 (Teaching Assistant)</option>
            <option value="3">讲师 (Lecturer)</option>
            <option value="4">副教授 (Associate Professor)</option>
            <option value="5">特任教授 (Distinguished Professor)</option>
            <option value="6">教授 (Professor)</option>
            <option value="7">助理研究员 (Assistant Researcher)</option>
            <option value="8">
              特任副研究员 (Distinguished Associate Researcher)
            </option>
            <option value="9">副研究员 (Associate Researcher)</option>
            <option value="10">特任研究员 (Distinguished Researcher)</option>
            <option value="11">研究员 (Researcher)</option>
          </Form.Control>
        </Form.Group>
        <Form.Group controlId="teacherPassword">
          <Form.Label>密码 (Password)</Form.Label>
          <Form.Control
            type="password"
            placeholder="请输入密码"
            value={newTeacher.password}
            onChange={(e) =>
              setNewTeacher({ ...newTeacher, password: e.target.value })
            }
            required
          />
        </Form.Group>
        <Button variant="primary" onClick={handleCreateTeacher}>
          创建教师
        </Button>
      </Form>
      <br />
      <br />
      <br />
    </div>
  );
};

export default TeacherForm;
