"use client";

import React, { useState } from "react";
import IdInput from "./IdInput";
import NameInput from "./NameInput";
import TotalHoursInput from "./TotalHoursInput";
import LevelInput from "./LevelInput";
import TaughtCoursesInput from "./TaughtCoursesInput";
import { useRouter } from "next/navigation";

const CreateCoursePage = () => {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [totalHours, setTotalHours] = useState(0);
  const [level, setLevel] = useState(1);
  const [taughtCourses, setTaughtCourses] = useState({});
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Group taughtCourses by year and term and validate teaching hours
    const groupedTeachingHours = {};

    for (const key in taughtCourses) {
      const { year, term, teachingHours } = taughtCourses[key];
      if (teachingHours <= 0) {
        setErrorMessage("Teaching hours must be greater than 0.");
        return;
      }
      const groupKey = `${year}-${term}`;
      if (!groupedTeachingHours[groupKey]) {
        groupedTeachingHours[groupKey] = 0;
      }
      groupedTeachingHours[groupKey] += teachingHours;
    }

    for (const key in groupedTeachingHours) {
      if (groupedTeachingHours[key] !== totalHours) {
        setErrorMessage(`Total teaching hours for ${key} do not match the specified total hours.`);
        return;
      }
    }

    const courseData = {
      id,
      name,
      totalHours,
      level,
      taughtCourses: Object.values(taughtCourses),
    };

    try {
      const res = await fetch("/api/courses/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(courseData),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessMessage("Course created successfully!");
        setTimeout(() => {
          router.push("/courses");
        }, 2000);
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Error creating course");
      }
    } catch (error) {
      setErrorMessage("An error occurred while creating the course.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-sm">
      <IdInput id={id} setId={setId} />
      <NameInput name={name} setName={setName} />
      <TotalHoursInput totalHours={totalHours} setTotalHours={setTotalHours} />
      <LevelInput level={level} setLevel={setLevel} />
      <TaughtCoursesInput taughtCourses={taughtCourses} setTaughtCourses={setTaughtCourses} />
      <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded-md">
        Create Course
      </button>
      {errorMessage && <p className="text-red-500 mt-4">{errorMessage}</p>}
      {successMessage && <p className="text-green-500 mt-4">{successMessage}</p>}
    </form>
  );
};

export default CreateCoursePage;
