import React from "react";

const courseLevels = {
  1: "本科生课程",
  2: "研究生课程",
};

const terms = {
  1: "春季学期",
  2: "夏季学期",
  3: "秋季学期",
};

const CourseList = ({ courses }) => (
  <div>
    <h3 className="text-lg font-semibold">课程</h3>
    {courses.length > 0 ? (
      <ul>
        {courses.map((course, index) => (
          <li key={index}>
            <h4>{course.course.name}</h4>
            <p>年份: {course.year}</p>
            <p>学期: {terms[course.term]}</p>
            <p>教学时长: {course.teachingHours}</p>
            <p>总时长: {course.course.totalHours}</p>
            <p>课程级别: {courseLevels[course.course.level]}</p>
          </li>
        ))}
      </ul>
    ) : (
      <p>没有找到课程</p>
    )}
  </div>
);

export default CourseList;
