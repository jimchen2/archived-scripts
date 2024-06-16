import React from "react";
import Link from "next/link";

interface BlogPreview {
  _id: string;
  title: string;
  date: string;
  body: string;
  type: string;
}

interface PreviewCardProps {
  blog: BlogPreview;
  highlightPattern?: string;
}

const highlight = (text: string, pattern?: string) =>
  pattern
    ? text.split(new RegExp(`(${pattern})`, "gi")).map((part, index) =>
        part.match(new RegExp(`(${pattern})`, "gi")) ? (
          <span key={index} className="bg-gray-300 font-bold">
            {part}
          </span>
        ) : (
          part
        )
      )
    : text;

const truncateText = (text: string, maxLength: number) =>
  text.length > maxLength ? text.substring(0, maxLength) + "..." : text;

const PreviewCard: React.FC<PreviewCardProps> = ({ blog, highlightPattern }) => (
  <Link href={`/blog/${blog.date}`}>
    <li className="bg-white shadow-lg rounded-lg p-6 cursor-pointer hover:bg-gray-50 max-w-screen-lg mx-auto transition duration-300 ease-in-out transform hover:-translate-y-1 hover:scale-105">
      <h2 className="text-2xl font-bold text-indigo-600 flex justify-between items-center">
        <span className="hover:underline">{blog.title}</span>{blog.type}
      </h2>
      <p className="text-gray-500 text-sm font-mono">{new Date(blog.date).toLocaleDateString()}</p>
      <p className="mt-4 text-gray-700 break-words truncate font-sans">{highlight(truncateText(blog.body, 150), highlightPattern)}</p>
    </li>
  </Link>
);

export default PreviewCard;
