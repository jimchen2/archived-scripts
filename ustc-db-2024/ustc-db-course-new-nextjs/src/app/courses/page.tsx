"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Course, fetchCourses, deleteCourse } from "./CourseApi";

const CoursesPage = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [searchId, setSearchId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const router = useRouter();

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async (id: string = "") => {
    setLoading(true);
    setError("");

    try {
      const data = await fetchCourses(id);
      setCourses(data);
    } catch (error) {
      setError("Failed to fetch courses");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    setLoading(true);
    setError("");

    try {
      await deleteCourse(id);
      loadCourses();
    } catch (error) {
      setError("Failed to delete course");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadCourses(searchId);
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">List of Courses</h1>
      <div className="mb-4">
        <input
          type="text"
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          placeholder="Search by ID"
          className="p-2 border border-gray-300 rounded-md mr-2"
        />
        <button
          onClick={handleSearch}
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
        >
          Search
        </button>
      </div>
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p>{error}</p>
      ) : (
        <ul className="list-disc pl-5">
          {courses.map((course) => (
            <li key={course.id} className="mb-4">
              <div className="border p-4 rounded-md shadow-md">
                <strong>ID:</strong> {course.id}
                <br />
                <strong>Name:</strong> {course.name}
                <br />
                <strong>Total Hours:</strong> {course.totalHours}
                <br />
                <strong>Level:</strong> {course.level === 1 ? "本科生课程" : "研究生课程"}
                <br />
                <em>Taught Courses:</em>
                <ul className="list-disc pl-5">
                  {course.taughtCourses.map((taughtCourse) => (
                    <li
                      key={`${taughtCourse.courseId}-${taughtCourse.teacherId}`}
                    >
                      Teacher: {taughtCourse.teacher.name} - Year:{" "}
                      {taughtCourse.year}, Term: {taughtCourse.term}, Teaching
                      Hours: {taughtCourse.teachingHours}
                    </li>
                  ))}
                </ul>
                <div className="flex space-x-2 mt-2">
                  <button
                    onClick={() => handleDelete(course.id)}
                    className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
                  >
                    Delete
                  </button>
                  <button
                    onClick={() => router.push(`/courses/edit/${course.id}`)}
                    className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded"
                  >
                    Edit
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default CoursesPage;
