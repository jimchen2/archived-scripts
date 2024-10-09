import React, { useState, useEffect } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";
import { Alert } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import { backendUrl } from "../../config";

const EditCourse = () => {
  const [year, setYear] = useState("");
  const [term, setTerm] = useState("");
  const [teachingHours, setTeachingHours] = useState("");
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    fetchCourse();
  }, []);

  const fetchCourse = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${backendUrl}/teachercourses`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const course = response.data;
      setYear(course.year);
      setTerm(course.term);
      setTeachingHours(course.teaching_hours);
    } catch (error) {
      console.error("获取课程信息时出错:", error);
      setError("获取课程信息时出错，请稍后重试。");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const token = localStorage.getItem("token");
      await axios.put(
        `${backendUrl}I/teachercourses/${courseId}`,
        {
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
      setSuccess("课程更新成功！");
      setError("");
      navigate("/courses");
    } catch (error) {
      console.error("更新课程信息时出错:", error);
      setError("更新课程信息时出错，请检查输入并重试。");
      setSuccess("");
    }
  };

  return (
    <div className="container">
      <h2>编辑授课信息</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
      <form onSubmit={handleSubmit}>
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
          更新课程
        </button>
      </form>
    </div>
  );
};

export default EditCourse;
