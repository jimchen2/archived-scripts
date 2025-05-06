import React from "react";

const TaughtCoursesInput = ({ taughtCourses, setTaughtCourses }) => {
  const handleAddCourse = () => {
    const newKey = `course_${Date.now()}`;
    setTaughtCourses({
      ...taughtCourses,
      [newKey]: {
        teacherId: "",
        year: new Date().getFullYear(),
        term: 1,
        teachingHours: 0,
      },
    });
  };

  const handleDeleteCourse = (key) => {
    const newTaughtCourses = { ...taughtCourses };
    delete newTaughtCourses[key];
    setTaughtCourses(newTaughtCourses);
  };

  const handleCourseChange = (key, field, value) => {
    setTaughtCourses({
      ...taughtCourses,
      [key]: { ...taughtCourses[key], [field]: value },
    });
  };

  return (
    <div className="mb-4">
      <label className="block text-gray-700 font-bold mb-2">Taught Courses:</label>
      {Object.keys(taughtCourses).map((key) => (
        <div key={key} className="mb-2 flex items-center space-x-2">
          <input
            type="text"
            placeholder="Teacher ID"
            value={taughtCourses[key].teacherId}
            onChange={(e) => handleCourseChange(key, "teacherId", e.target.value)}
            required
            maxLength={5}
            className="w-1/5 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <input
            type="number"
            placeholder="Year"
            value={taughtCourses[key].year}
            onChange={(e) => handleCourseChange(key, "year", parseInt(e.target.value))}
            className="w-1/5 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <select
            value={taughtCourses[key].term}
            onChange={(e) => handleCourseChange(key, "term", parseInt(e.target.value))}
            required
            className="w-1/5 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value={1}>1 - 春季学期</option>
            <option value={2}>2 - 夏季学期</option>
            <option value={3}>3 - 秋季学期</option>
          </select>
          <input
            type="number"
            placeholder="Teaching Hours"
            value={taughtCourses[key].teachingHours}
            onChange={(e) => handleCourseChange(key, "teachingHours", parseInt(e.target.value))}
            required
            className="w-1/5 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="button"
            onClick={() => handleDeleteCourse(key)}
            className="px-3 py-2 bg-red-500 text-white rounded-md"
          >
            Delete
          </button>
        </div>
      ))}
      <button type="button" onClick={handleAddCourse} className="px-3 py-2 bg-blue-500 text-white rounded-md mt-2">
        Add Course
      </button>
    </div>
  );
};

export default TaughtCoursesInput;
