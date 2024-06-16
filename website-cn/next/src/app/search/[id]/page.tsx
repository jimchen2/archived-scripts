"use client";

import { useParams } from "next/navigation";
import React, { useEffect, useState } from "react";
import PreviewCard from "./PreviewCard";

interface BlogPreview {
  _id: string;
  title: string;
  date: string;
  body: string;
  type: string;
}

const BlogPreview = () => {
  const params = useParams();
  const id = params?.id as string;

  const [blogPreviews, setBlogPreviews] = useState<BlogPreview[]>([]);

  useEffect(() => {
    const fetchBlogPreviews = async () => {
      const res = await fetch(`/api/searchBlog?query=${id}`);
      const data: BlogPreview[] = await res.json();
      setBlogPreviews(data);
    };

    fetchBlogPreviews();
  }, [id]);

  return (
    <div className="container mx-auto px-4 py-8">
      <br />
      <br />
      <br />
      <ul className="space-y-4 overflow-hidden">
        {blogPreviews.map((blog) => (
          <PreviewCard key={blog._id} blog={blog} highlightPattern={id} />
        ))}
      </ul>
    </div>
  );
};

export default BlogPreview;
