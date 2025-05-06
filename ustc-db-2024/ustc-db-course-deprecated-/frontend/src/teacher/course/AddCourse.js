import React, { useState } from "react";
import axios from "axios";
import CourseForm from "./CourseForm";
import { Alert } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import { backendUrl } from "../../config";

const AddCourse = () => {
  const [courseId, setCourseId] = useState("");
  const [year, setYear] = useState("");
  const [term, setTerm] = useState("");
  const [teachingHours, setTeachingHours] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem("token");
      await axios.post(
        `${backendUrl}/teachercourses`,
        {
          course_id: courseId,
          year: parseInt(year),
          term: parseInt(term),
          teaching_hours: parseInt(teachingHours),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setCourseId("");
      setYear("");
      setTerm("");
      setTeachingHours("");
      setError("");
      setSuccess("Course added successfully!");
    } catch (error) {
      setError(error.response.data);
      setSuccess("");
      console.error("Error adding course:", error);
    }
  };

  return (
    <div className="container">
      <h2>Add Taught Course</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      <CourseForm
        courseId={courseId}
        setCourseId={setCourseId}
        year={year}
        setYear={setYear}
        term={term}
        setTerm={setTerm}
        teachingHours={teachingHours}
        setTeachingHours={setTeachingHours}
        handleSubmit={handleSubmit}
      />
    </div>
  );
};

export default AddCourse;
