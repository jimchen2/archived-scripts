import React, { useEffect, useState } from "react";
import axios from "axios";
import CourseForm from "./CourseForm";
import CourseTable from "./CourseTable";
import { backendUrl } from "../../config";

const CourseManagement = () => {
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await axios.get(`${backendUrl}/courses`);
      setCourses(response.data);
    } catch (error) {
      console.error("Failed to fetch courses:", error);
    }
  };

  const handleCourseCreated = () => {
    fetchCourses();
  };

  const handleDeleteCourse = async (courseId) => {
    try {
      await axios.delete(`${backendUrl}/courses/${courseId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      fetchCourses();
    } catch (error) {
      console.error("Failed to delete course:", error);
    }
  };

  return (
    <div>
      <h2>Course Management</h2>
      <CourseForm onCourseCreated={handleCourseCreated} />
      <CourseTable courses={courses} onDeleteCourse={handleDeleteCourse} />
    </div>
  );
};

export default CourseManagement;
