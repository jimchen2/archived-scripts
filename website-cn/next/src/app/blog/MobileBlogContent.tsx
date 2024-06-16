import React, { useEffect, useState } from "react";
import { MathJax, MathJaxContext } from "better-react-mathjax";
import TableOfContents from "./TableOfContents";
import "./blog.css";

interface BlogContentProps {
  title: string;
  type: string;
  date: string;
  body: string;
}

interface Heading {
  id: string;
  text: string; // Ensure text is always a string
  tagName: string;
}

function extractHeadings(html: string): Heading[] {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  const headings = Array.from(tmp.querySelectorAll("h2")).map((heading) => ({
    id: heading.id,
    text: heading.textContent || "", // Ensure text is always a string
    tagName: heading.tagName,
  }));
  return headings;
}

const BlogContent: React.FC<BlogContentProps> = ({
  title,
  type,
  date,
  body,
}) => {
  const [headings, setHeadings] = useState<Heading[]>([]);

  useEffect(() => {
    // Scroll to the hash if present
    if (window.location.hash) {
      const elementId = window.location.hash.substring(1).toLowerCase();
      const element = document.getElementById(elementId);
      if (element) {
        element.scrollIntoView();
        setTimeout(() => {
          window.scrollBy(0, -35);
        }, 100); // Adjust the delay as needed
      }
    }

    // Extract headings
    setHeadings(extractHeadings(body));
  }, [body]);

  return (
    <MathJaxContext>
      <br />
      <br />
      <br />

      <div className="blog-content-container overflow-hidden">
        <div className="flex flex-col lg:flex-row">
          <br />
          <br />
          <div className="lg:w-1/4 lg:pl-8 lg:sticky lg:top-20">
            <TableOfContents headings={headings} />
          </div>

          <div className="max-w-3xl mx-auto p-4 flex-grow">
            <h1 className="text-3xl font-bold mb-4">{title}</h1>
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-4">
                {new Date(date).toLocaleDateString()}
              </p>
            </div>
            <div className="prose lg:prose-xl break-words">
              <MathJax>
                <div className="scoped-styles">
                  <div
                    className="break-words"
                    dangerouslySetInnerHTML={{ __html: body }}
                  />
                </div>
              </MathJax>
            </div>
            <br />
            <span className="inline-block bg-gray-300 text-black-200 text-xs px-2 py-1 rounded-full">
              {type}
            </span>
          </div>
        </div>
      </div>
    </MathJaxContext>
  );
};

export default BlogContent;
