"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Teacher,
  fetchTeachers,
  handleDelete,
  getGender,
  getTitle,
} from "./teacherHelpers";

const TeachersPage = () => {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [searchId, setSearchId] = useState("");

  useEffect(() => {
    fetchTeachers(setTeachers);
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchId(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTeachers(setTeachers, searchId);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">
        <Link href={`/teachers/create`}>教师</Link>
      </h1>
      <form onSubmit={handleSearchSubmit} className="mb-4">
        <input
          type="text"
          placeholder="按ID搜索"
          value={searchId}
          onChange={handleSearchChange}
          className="p-2 border border-gray-300 rounded-md mr-2"
        />
        <button
          type="submit"
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
        >
          搜索
        </button>
      </form>
      <ul className="list-disc pl-5">
        {teachers.map((teacher) => (
          <li
            key={teacher.id}
            className="mb-2 flex items-center justify-between"
          >
            <div>
              <div className="font-bold">{teacher.name}</div>
              <div>ID: {teacher.id}</div>
              <div>性别: {getGender(teacher.gender)}</div>
              <div>职称: {getTitle(teacher.title)}</div>
            </div>
            <div>
              <Link
                href={`/teachers/edit/${teacher.id}`}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-1 px-3 rounded mr-2"
              >
                编辑
              </Link>
              <button
                onClick={() => handleDelete(teacher.id, setTeachers)}
                className="bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-3 rounded"
              >
                删除
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TeachersPage;
