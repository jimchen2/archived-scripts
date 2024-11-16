import ReactMarkdown from "react-markdown";
import "katex/dist/katex.min.css";
import { InlineMath, BlockMath } from "react-katex";
import Image from "next/image";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw"; // Add this import

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const components = {
    h2: ({ children }: { children: React.ReactNode }) => <h2 className="text-xl font-bold">{children}</h2>,

    h3: ({ children }: { children: React.ReactNode }) => <h3 className="text-lg font-medium">{children}</h3>,

    p: ({ children }: { children: React.ReactNode }) => <div className="text-base">{children}</div>,

    math: ({ value }: { value: string }) => <BlockMath math={value} />,

    inlineMath: ({ value }: { value: string }) => <InlineMath math={value} />,

    img: ({ src, alt }: { src: string; alt: string }) => <Image src={src} alt={alt || "Post image"} width={800} height={400} className="my-4" />,

    code: ({ node, inline, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || "");
      return !inline && match ? (
        <SyntaxHighlighter language={match[1]} PreTag="div" className="whitespace-pre-wrap break-words overflow-x-auto" {...props}>
          {String(children).replace(/\n$/, "")}
        </SyntaxHighlighter>
      ) : (
        <code className={`${className} whitespace-pre-wrap break-words`} {...props}>
          {children}
        </code>
      );
    },
  };

  return (
    <ReactMarkdown
      components={components}
      remarkPlugins={[remarkMath]}
      rehypePlugins={[rehypeKatex, rehypeRaw]} // Add rehypeRaw here
    >
      {content}
    </ReactMarkdown>
  );
}
