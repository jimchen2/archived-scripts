"use client";

import { useParams } from "next/navigation";
import React, { useEffect, useState } from "react";
import PreviewCard from "./PreviewCard";

interface DocumentSnippet {
  title: string;
  date: string;
  type: string;
  body: string;
  isTitleMatch: boolean;
  isBodyMatch: boolean;
}

const BlogPreview = () => {
  const params = useParams();
  const query = params?.id as string;

  const [documentSnippets, setDocumentSnippets] = useState<DocumentSnippet[]>([]);

  useEffect(() => {
    const fetchDocumentSnippets = async () => {
      const res = await fetch(`/api/searchBlog${query ? `?query=${query}` : ""}`);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data: DocumentSnippet[] = await res.json();
      setDocumentSnippets(data);
    };

    fetchDocumentSnippets();
  }, [query]);

  return (
    <div className="container mx-auto px-4 py-8">
      <br />
      <br />
      <br />
      <br />
      <ul className="space-y-4">
        {documentSnippets.map((doc, index) => (
          <PreviewCard key={index} document={doc} highlightPattern={query} />
        ))}
      </ul>
    </div>
  );
};

export default BlogPreview;
