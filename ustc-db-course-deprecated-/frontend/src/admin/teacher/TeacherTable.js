import React from "react";
import { Table, Button } from "react-bootstrap";

const genderMap = {
  1: "男性 (Male)",
  2: "女性 (Female)",
  3: "双性 (Intersex)",
  4: "非二元性别 (Non-binary)",
  5: "性别酷儿 (Genderqueer)",
  6: "性别流动 (Genderfluid)",
  7: "无性别 (Agender)",
  8: "双性别 (Bigender)",
  9: "性别多样 (Gender diverse)",
  10: "双魂 (Two-Spirit)"
};

const titleMap = {
  1: "博士后 (Postdoctoral)",
  2: "助教 (Teaching Assistant)",
  3: "讲师 (Lecturer)",
  4: "副教授 (Associate Professor)",
  5: "特任教授 (Distinguished Professor)",
  6: "教授 (Professor)",
  7: "助理研究员 (Assistant Researcher)",
  8: "特任副研究员 (Distinguished Associate Researcher)",
  9: "副研究员 (Associate Researcher)",
  10: "特任研究员 (Distinguished Researcher)",
  11: "研究员 (Researcher)"
};

const TeacherTable = ({ teachers, onDeleteTeacher }) => {
  return (
    <Table striped bordered hover>
      <thead>
        <tr>
          <th>工号 (ID)</th>
          <th>姓名 (Name)</th>
          <th>性别 (Gender)</th>
          <th>职称 (Title)</th>
          <th>操作 (Actions)</th>
        </tr>
      </thead>
      <tbody>
        {teachers.map((teacher) => (
          <tr key={teacher.id}>
            <td>{teacher.id}</td>
            <td>{teacher.name}</td>
            <td>{genderMap[teacher.gender]}</td>
            <td>{titleMap[teacher.title]}</td>
            <td>
              <Button
                variant="danger"
                onClick={() => onDeleteTeacher(teacher.id)}
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

export default TeacherTable;
