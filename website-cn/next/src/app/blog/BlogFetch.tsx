"use client";

import { useEffect, useState } from "react";
import BlogContent from "./BlogContent"; // Import the BlogContent component
import MobileBlogContent from "./MobileBlogContent"; // Import the MobileBlogContent component

interface Post {
  body: string;
  title: string;
  type: string;
  date: string;
}

interface BlogPostProps {
  mobile: boolean;
  id: string; // Add 'id' to the component's props
}

const BlogFetch: React.FC<BlogPostProps> = ({ mobile, id }) => {
  const [post, setPost] = useState<Post[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetch(`/api/getBlog?date=${id}`)
        .then((res) => res.json())
        .then((data) => {
          setPost(data);
          setLoading(false);
        })
        .catch((error) => {
          console.error("Failed to fetch post:", error);
          setLoading(false);
        });
    }
  }, [id]); 
  
  if (loading) {
    return <div className="text-center text-gray-500">Loading...</div>;
  }

  if (!post || post.length === 0) {
    return <div className="text-center text-gray-500">No post found</div>;
  }

  return (
    <div>
      {mobile ? (
        <MobileBlogContent
          title={post[0].title}
          type={post[0].type}
          date={post[0].date}
          body={post[0].body}
        />
      ) : (
        <BlogContent
          title={post[0].title}
          type={post[0].type}
          date={post[0].date}
          body={post[0].body}
        />
      )}
    </div>
  );
};

export default BlogFetch;