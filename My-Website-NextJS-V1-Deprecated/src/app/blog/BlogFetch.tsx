"use client";

import { useEffect, useState } from "react";
import BlogContent from "./BlogContent";
import MobileBlogContent from "./MobileBlogContent";

interface Post {
  _id: string;
  title: string;
  date: Date;
  type: string;
  body: string;
}

interface BlogPostProps {
  mobile: boolean;
  title: string;
  type?: string;
}

const BlogFetch: React.FC<BlogPostProps> = ({ mobile, title, type }) => {
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (title) {
      let url = `/api/getBlog?title=${encodeURIComponent(title)}`;

      if (type) {
        url += `&type=${encodeURIComponent(type)}`;
      }

      fetch(url)
        .then((res) => res.json())
        .then((data) => {
          if (data.message) {
            // Handle case where no post is found
            setPost(null);
          } else {
            setPost({
              ...data,
              date: new Date(data.date),
            });
          }
          setLoading(false);
        })
        .catch((error) => {
          console.error("Failed to fetch post:", error);
          setLoading(false);
        });
    }
  }, [title, type]);

  if (loading) {
    return <div className="text-center text-gray-500">Loading...</div>;
  }

  if (!post) {
    return <div className="text-center text-gray-500">No post found</div>;
  }

  return (
    <div>
      {mobile ? (
        <MobileBlogContent title={post.title} type={post.type} date={post.date} body={post.body} />
      ) : (
        <BlogContent title={post.title} type={post.type} date={post.date} body={post.body} />
      )}
    </div>
  );
};

export default BlogFetch;