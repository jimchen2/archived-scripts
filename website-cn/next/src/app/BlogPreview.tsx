"use client";
import React, { useEffect, useState } from "react";
import { ChevronDownIcon } from "@heroicons/react/solid";

interface BlogPreview {
  _id: string;
  title: string;
  date: string;
  uuid: string;
  body: string;
  type: string;
}

interface BlogType {
  type: string;
  blogs: BlogPreview[];
}

interface BlogPreviewProps {
  newlines?: number;
  fontSize?: string;
  onSelectBlogId: (uuid: string) => void;
}

const BlogPreview: React.FC<BlogPreviewProps> = React.memo(
  ({ newlines = 4, fontSize = "text-2xl", onSelectBlogId }) => {
    const [blogPreviews, setBlogPreviews] = useState<BlogType[]>([]);
    const [openDropdowns, setOpenDropdowns] = useState<{
      [key: string]: boolean;
    }>({});
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
      const fetchBlogPreviews = async () => {
        try {
          const res = await fetch("/api/previewBlog");
          if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
          const data: BlogType[] = await res.json();
          setBlogPreviews(data);
        } catch (error) {
          console.error("Failed to fetch blog previews:", error);
          setError("Failed to load blogs. Please try again later.");
        }
      };

      fetchBlogPreviews();
    }, []);

    const toggleDropdown = (type: string) => {
      setOpenDropdowns((prevOpenDropdowns) => ({
        ...prevOpenDropdowns,
        [type]: !prevOpenDropdowns[type],
      }));
    };

    const handleSelectBlog = (uuid: string) => {
      onSelectBlogId(uuid);
    };

    const renderNewlines = () => {
      return Array.from({ length: newlines }).map((_, idx) => <br key={idx} />);
    };

    return (
      <div className="flex flex-col md:flex-row gap-4 p-4">
        <div className="w-full sticky top-0">
          {renderNewlines()}
          <header className={`${fontSize} font-bold p-4 text-center`}>
            我的博客
          </header>
          {error ? (
            <div className="text-center">{error}</div>
          ) : (
            <ul className="space-y-4 overflow-x-hidden">
              {blogPreviews.map((blogType) => (
                <li key={blogType.type}>
                  <div className="rounded-lg shadow-lg p-4 transition duration-300 ease-in-out transform bg-gray-50">
                    <div
                      className="flex justify-between items-center cursor-pointer"
                      onClick={() => toggleDropdown(blogType.type)}
                    >
                      <h4 className="ml-[5%] font-medium text-gray-800">
                        {blogType.type} ({blogType.blogs.length})
                      </h4>
                      <ChevronDownIcon
                        className={`h-5 w-5 text-gray-800 duration-300 ${
                          openDropdowns[blogType.type]
                            ? "rotate-180"
                            : "rotate-0"
                        }`}
                      />
                    </div>
                    {openDropdowns[blogType.type] && (
                      <ul className="mt-2 space-y-2">
                        {blogType.blogs.map((blog) => (
                          <li
                            key={blog._id}
                            className="p-4 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 hover:underline"
                            onClick={() => handleSelectBlog(blog.uuid)}
                          >
                            <div className="flex justify-center">
                              <h6 className="font-semibold text-gray-700 text-center">
                                {blog.title}
                              </h6>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </li>
              ))}
              {renderNewlines()}
            </ul>
          )}
        </div>
      </div>
    );
  }
);

export default BlogPreview;