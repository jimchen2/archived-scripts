import React, { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { backendUrl } from "../../config";

const CourseList = () => {
  const [courses, setCourses] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredCourses, setFilteredCourses] = useState([]);

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    setFilteredCourses(
      courses.filter(
        (course) =>
          course.course_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          course.year.toString().includes(searchTerm) ||
          course.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
          course.teaching_hours.toString().includes(searchTerm)
      )
    );
  }, [searchTerm, courses]);

  const fetchCourses = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${backendUrl}/teachercourses`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setCourses(response.data);
    } catch (error) {
      console.error("Error fetching courses:", error);
    }
  };

  const handleDelete = async (courseId) => {
    try {
      const token = localStorage.getItem("token");
      await axios.delete(`${backendUrl}/teachercourses/${courseId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchCourses();
    } catch (error) {
      console.error("Error deleting course:", error);
    }
  };

  return (
    <div className="container">
      <h2>Taught Courses</h2>
      <input
        type="text"
        placeholder="Search courses..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="form-control mb-3"
      />
      <table className="table">
        <thead>
          <tr>
            <th>Course ID</th>
            <th>Year</th>
            <th>Term</th>
            <th>Teaching Hours</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredCourses.map((course) => (
            <tr key={course.course_id}>
              <td>{course.course_id}</td>
              <td>{course.year}</td>
              <td>{course.term}</td>
              <td>{course.teaching_hours}</td>
              <td>
                <Link
                  to={`/course/edit/${course.course_id}`}
                  className="btn btn-warning me-2"
                >
                  Edit
                </Link>
                <button
                  className="btn btn-danger"
                  onClick={() => handleDelete(course.course_id)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CourseList;
