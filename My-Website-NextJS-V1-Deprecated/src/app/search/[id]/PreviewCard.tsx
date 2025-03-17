import React from "react";
import Link from "next/link";

interface BlogPreview {
  title: string;
  date: string;
  type: string;
  body: string;
  isTitleMatch: boolean;
  isBodyMatch: boolean;
}

interface PreviewCardProps {
  document: BlogPreview;
  highlightPattern?: string;
}

const highlight = (text: string, pattern?: string) =>
  pattern
    ? text.split(new RegExp(`(${pattern})`, "gi")).map((part, index) =>
        part.toLowerCase() === pattern.toLowerCase() ? (
          <span key={index} className="font-black bg-yellow-200">
            {part}
          </span>
        ) : (
          part
        )
      )
    : text;

const PreviewCard: React.FC<PreviewCardProps> = ({
  document,
  highlightPattern,
}) => {
  const linkHref = `/?title=${document.title}`;

  return (
    <li className="shadow-lg rounded-lg p-6 max-w-screen-lg mx-auto transition hover:bg-gray-200">
      <h2 className="text-2xl font-bold text-gray-800 flex justify-between items-center">
        <Link href={linkHref}>
          <span className="hover:underline">
            {highlight(document.title, highlightPattern)}
          </span>
        </Link>
        <span className="text-sm bg-gray-200 px-2 py-1 rounded">
          {highlight(document.type, highlightPattern)}
        </span>
      </h2>
      <p className="text-gray-500 text-sm font-mono">
        {highlight(new Date(document.date).toLocaleDateString(), highlightPattern)}
      </p>
      <p className="mt-4 text-gray-700 break-words font-sans">
        {highlight(document.body, highlightPattern)}
      </p>
    </li>
  );
};

export default PreviewCard;