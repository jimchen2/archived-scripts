import React, { useState, useEffect } from "react";
import axios from "axios";
import { backendUrl } from "../../config";

const CourseForm = ({
  courseId,
  setCourseId,
  year,
  setYear,
  term,
  setTerm,
  teachingHours,
  setTeachingHours,
  handleSubmit,
}) => {
  const [availableCourses, setAvailableCourses] = useState([]);

  useEffect(() => {
    fetchAvailableCourses();
  }, []);

  const fetchAvailableCourses = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${backendUrl}/courses`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setAvailableCourses(response.data);
    } catch (error) {
      console.error("Error fetching available courses:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-3">
        <label htmlFor="courseId" className="form-label">
          课程编号
        </label>
        <select
          className="form-control"
          id="courseId"
          value={courseId}
          onChange={(e) => setCourseId(e.target.value)}
        >
          <option value="">请选择课程</option>
          {availableCourses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.id}
            </option>
          ))}
        </select>
      </div>
      <div className="mb-3">
        <label htmlFor="year" className="form-label">
          年份
        </label>
        <input
          type="number"
          className="form-control"
          id="year"
          value={year}
          onChange={(e) => setYear(e.target.value)}
        />
      </div>
      <div className="mb-3">
        <label htmlFor="term" className="form-label">
          学期
        </label>
        <select
          className="form-control"
          id="term"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        >
          <option value="">请选择学期</option>
          <option value="1">1-春季学期</option>
          <option value="2">2-夏季学期</option>
          <option value="3">3-秋季学期</option>
        </select>
      </div>
      <div className="mb-3">
        <label htmlFor="teachingHours" className="form-label">
          教学小时
        </label>
        <input
          type="number"
          className="form-control"
          id="teachingHours"
          value={teachingHours}
          onChange={(e) => setTeachingHours(e.target.value)}
        />
      </div>
      <button type="submit" className="btn btn-primary">
        添加课程
      </button>
    </form>
  );
};

export default CourseForm;
