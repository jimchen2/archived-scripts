"use client";
import React, { useState } from "react";
import SearchForm from "./SearchForm";
import PaperList from "./PaperList";
import ProjectList from "./ProjectList";
import CourseList from "./CourseList";
import { exportToPDF } from "./ExportPDF";
import { exportToExcel } from "./ExportExcel";
import { exportToWord } from "./ExportWord";

// Define the interfaces
interface Paper {
  paper: {
    id: number;
    name: string;
    source: string;
    year: number;
    type: number;
    level: number;
  };
  ranking: number;
  isCorrespondingAuthor: boolean;
}

interface Project {
  project: {
    id: string;
    name: string;
    source: string;
    projectType: number;
    totalFunding: number;
    startYear: number;
    endYear: number;
  };
  ranking: number;
  funding: number;
}

interface Course {
  course: {
    id: string;
    name: string;
    totalHours: number;
    level: number;
  };
  year: number;
  term: number;
  teachingHours: number;
}

interface TeacherResults {
  publishedPapers: Paper[];
  projectParticipants: Project[];
  taughtCourses: Course[];
}

const SearchPage = () => {
  const [results, setResults] = useState<TeacherResults | null>(null);
  const [error, setError] = useState("");

  const handleSearch = async (
    teacherId: string,
    startYear: string,
    endYear: string
  ) => {
    setError("");
    try {
      const response = await fetch(
        `/api/search/search?teacherId=${teacherId}&startYear=${startYear}&endYear=${endYear}`
      );
      const data = await response.json();
      console.log(data);
      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch data");
      }
      setResults(data.teacher);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">搜索教师的学术活动</h1>
      <SearchForm onSearch={handleSearch} />
      {error && <p className="text-red-500 mt-4">{error}</p>}
      {results && (
        <div className="mt-8">
          <h2 className="text-xl font-bold mb-4">结果</h2>
          <PaperList papers={results.publishedPapers} />
          <ProjectList projects={results.projectParticipants} />
          <CourseList courses={results.taughtCourses} />
          <div className="mt-4">
            <button
              className="bg-blue-500 text-white py-2 px-4 mr-2 rounded"
              onClick={() => exportToPDF(results)}
            >
              导出为 PDF
            </button>
            <button
              className="bg-green-500 text-white py-2 px-4 mr-2 rounded"
              onClick={() => exportToExcel(results)}
            >
              导出为 Excel
            </button>
            <button
              className="bg-purple-500 text-white py-2 px-4 rounded"
              onClick={() => exportToWord(results)}
            >
              导出为 Word
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchPage;
