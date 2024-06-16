"use client";
import React from "react";
import Link from "next/link";

const JimChenWebsite: React.FC = () => {
  return (
    <>
      <Link
        href="/"
        className=" text-lg text-gray-800 dark:text-white hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-300"
      >
        陈加木的个人主页
      </Link>
    </>
  );
};

export default JimChenWebsite;
