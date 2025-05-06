import React, { useState, useEffect } from "react";
import axios from "axios";
import { Table, Button, Form, FormControl } from "react-bootstrap";
import TeacherForm from "./TeacherForm";
import TeacherTable from "./TeacherTable";
import { backendUrl } from "../../config";

const Teachers = () => {
  const [teachers, setTeachers] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchTeachers();
  }, []);

  const fetchTeachers = async () => {
    try {
      const response = await axios.get(`${backendUrl}/teachers`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      setTeachers(response.data);
    } catch (error) {
      console.error("Failed to fetch teachers:", error);
      setTeachers([]);
      alert("Failed to fetch teachers. Please try again.");
    }
  };

  const handleDeleteTeacher = async (teacherId) => {
    try {
      await axios.delete(`${backendUrl}/teachers/${teacherId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      fetchTeachers();
    } catch (error) {
      console.error("Failed to delete teacher:", error);
      alert(error);
    }
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const normalizedTeachers = Array.isArray(teachers) ? teachers : [teachers];
  const filteredTeachers = normalizedTeachers.filter((teacher) =>
    teacher.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <h2>Teachers</h2>
      <TeacherForm onTeacherCreated={fetchTeachers} />

      <Form inline>
        <FormControl
          type="text"
          placeholder="Search by name"
          value={searchTerm}
          onChange={handleSearch}
        />
      </Form>
      <TeacherTable
        teachers={filteredTeachers}
        onDeleteTeacher={handleDeleteTeacher}
      />
    </div>
  );
};

export default Teachers;
