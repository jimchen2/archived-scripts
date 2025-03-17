import React, { useEffect, useState, useRef } from "react";
import { marked } from "marked";
import katex from "katex";
import "katex/dist/katex.min.css";
import TableOfContents from "./MobileTableOfContents";
import "./blog.css";

interface BlogContentProps {
  title: string;
  type: string;
  date: Date;
  body: string;
}

interface Heading {
  id: string;
  text: string;
  level: number;
}

function extractHeadings(html: string): Heading[] {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  const headings = Array.from(tmp.querySelectorAll("h2, h3, h4, h5, h6")).map((heading) => ({
    id: heading.id,
    text: heading.textContent || "",
    level: parseInt(heading.tagName.charAt(1)),
  }));
  return headings;
}

const BlogContent: React.FC<BlogContentProps> = ({ title, type, date, body }) => {
  const [headings, setHeadings] = useState<Heading[]>([]);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const renderLatex = (html: string) => {
      const codeBlocks: string[] = [];

      const htmlWithoutCode = html.replace(/(<pre><code>[\s\S]*?<\/code><\/pre>)|(<code>[^<]+<\/code>)/g, (match) => {
        codeBlocks.push(match);
        return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
      });

      const processedHtml = htmlWithoutCode.replace(/\$\$(.*?)\$\$|\$(.*?)\$/g, (match, block, inline) => {
        const latex = block || inline;
        const displayMode = !!block;
        try {
          return katex.renderToString(latex, { displayMode });
        } catch (error) {
          console.error("KaTeX error:", error);
          return match;
        }
      });

      return processedHtml.replace(/__CODE_BLOCK_(\d+)__/g, (_, index) => codeBlocks[parseInt(index)]);
    };

    const renderMarkdown = () => {
      if (contentRef.current) {
        const renderer = new marked.Renderer();
        let headingCounter = 0;
        renderer.heading = (text, level) => {
          headingCounter++;
          const escapedText = text.toLowerCase().replace(/[^\w]+/g, "-");
          const uniqueId = `${escapedText}-${level}-${headingCounter}`;
          return `<h${level} id="${uniqueId}">${text}</h${level}>`;
        };
    
        marked.use({ renderer });
    
        const renderedMarkdown = marked(body);
        const htmlWithLatex = renderLatex(renderedMarkdown);
        contentRef.current.innerHTML = htmlWithLatex;
        setHeadings(extractHeadings(htmlWithLatex));
      }
    };
    
    renderMarkdown();

    if (window.location.hash) {
      const elementId = window.location.hash.substring(1).toLowerCase();
      const element = document.getElementById(elementId);
      if (element) {
        element.scrollIntoView();
        setTimeout(() => {
          window.scrollBy(0, -35);
        }, 100);
      }
    }
  }, [body]);

  return (
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
            <p className="text-sm text-gray-500 mb-4">{new Date(date).toLocaleDateString()}</p>
          </div>
          <div className="font-opensans scopedStyles prose lg:prose-xl break-words">
            <div ref={contentRef} className="break-words" />
          </div>
          <br />
          <span className="inline-block bg-gray-300 text-black-200 text-xs px-2 py-1 rounded-full">{type}</span>
        </div>
      </div>
    </div>
  );
};

export default BlogContent;