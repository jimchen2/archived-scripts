"use client";
import React, { useEffect, useState } from "react";
import BlogFetch from "./blog/BlogFetch";
import BlogPreview from "./BlogPreview";
import { useSearchParams, useRouter } from "next/navigation";

const BlogManager: React.FC = () => {
  const [mobile, setMobile] = useState(false);
  const router = useRouter();
  const params = useSearchParams();
  const urlTitle = params.get("title");

  const [selectedBlogTitle, setSelectedBlogTitle] = useState(urlTitle || "My New Website");

  useEffect(() => {
    const handleResize = () => {
      setMobile(window.innerWidth < 800);
    };
    window.addEventListener("resize", handleResize);
    handleResize();
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  useEffect(() => {
    if (urlTitle && urlTitle !== selectedBlogTitle) {
      setSelectedBlogTitle(urlTitle);
    }
  }, [urlTitle]);

  const handleSelectBlogId = (title: string) => {
    setSelectedBlogTitle(title);
    router.push(`/?title=${encodeURIComponent(title)}`, undefined, { shallow: true });
  };

  return (
    <div className="flex min-h-screen">
      {mobile ? (
        <div>
          <BlogFetch mobile={mobile} title={selectedBlogTitle} />
          <BlogPreview
            mobile={mobile}
            newlines={4}
            onSelectBlogId={handleSelectBlogId}
          />
        </div>
      ) : (
        <div className="flex">
          <div className="w-[320px] sticky top-0 h-screen overflow-y-auto">
            <BlogPreview
              mobile={mobile}
              newlines={2}
              fontSize="text-lg"
              onSelectBlogId={handleSelectBlogId}
            />
          </div>
          <div>
            <BlogFetch mobile={mobile} title={selectedBlogTitle} />
          </div>
        </div>
      )}
    </div>
  );
};

export default BlogManager;
