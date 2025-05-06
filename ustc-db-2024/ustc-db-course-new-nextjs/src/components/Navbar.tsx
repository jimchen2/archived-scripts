"use client";

import React, { useState } from "react";
import Link from "next/link";

const Navigation = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="bg-white fixed top-0 w-full z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-black font-bold text-lg">
              ustc-db-hw
            </Link>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link
                  href="/teachers"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Teachers
                </Link>
                <Link
                  href="/teachers/create"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Create Teacher
                </Link>
                <Link
                  href="/courses"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Courses
                </Link>
                <Link
                  href="/courses/create"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Create Course
                </Link>
                <Link
                  href="/papers"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Papers
                </Link>
                <Link
                  href="/papers/create"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Create Paper
                </Link>
                <Link
                  href="/projects"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Projects
                </Link>
                <Link
                  href="/projects/create"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Create Project
                </Link>
                <Link
                  href="/search"
                  className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
                >
                  Search
                </Link>
              </div>
            </div>
          </div>
          <div className="block md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Menu
            </button>
          </div>
        </div>
      </div>
      {isOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link
              href="/teachers"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Teachers
            </Link>
            <Link
              href="/teachers/create"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Create Teacher
            </Link>
            <Link
              href="/courses"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Courses
            </Link>
            <Link
              href="/courses/create"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Create Course
            </Link>
            <Link
              href="/papers"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Papers
            </Link>
            <Link
              href="/papers/create"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Create Paper
            </Link>
            <Link
              href="/projects"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Projects
            </Link>
            <Link
              href="/projects/create"
              className="block text-gray-800 hover:bg-gray-200 hover:text-black px-3 py-2 rounded-md text-sm font-medium"
            >
              Create Project
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
