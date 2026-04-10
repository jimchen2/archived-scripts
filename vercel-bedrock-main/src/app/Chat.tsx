import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import "./markdownStyles.css";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatProps {
  messages: Message[];
  currentAssistantMessage: string;
  isLoading: boolean;
  error: string | null;
  input: string;
  setInput: (input: string) => void;
  handleSubmit: (e: React.FormEvent) => void;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button onClick={handleCopy} className="absolute top-2 right-2 bg-black text-white px-2 py-1 rounded text-sm">
      {copied ? "Copied" : "Copy"}
    </button>
  );
};

const Chat: React.FC<ChatProps> = ({ messages, currentAssistantMessage, isLoading, error, input, setInput, handleSubmit, messagesEndRef }) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((m, index) => (
          <div key={index} className={`mb-4 max-w-full`}>
            {m.role === "user" ? (
              <div className="bg-gray-300 p-2 rounded-lg max-w-full">
                <code className="block whitespace-pre-wrap break-words text-black">{m.content}</code>
              </div>
            ) : (
              <div className="inline-block p-2 rounded-lg bg-gray-200 text-black markdown-content max-w-full">
                <ReactMarkdown
                  children={m.content}
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || "");
                      return !inline ? (
                        <div className="relative">
                          <CopyButton text={String(children).replace(/\n$/, "")} />
                          <SyntaxHighlighter language={match ? match[1] : undefined} PreTag="div" {...props} style={{ overflow: "auto", maxWidth: "100%" }}>
                            {String(children).replace(/\n$/, "")}
                          </SyntaxHighlighter>
                        </div>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                />
              </div>
            )}
          </div>
        ))}
        {currentAssistantMessage && (
          <div className="mb-4 text-left max-w-full">
            <div className="inline-block p-2 rounded-lg bg-gray-200 text-black markdown-content max-w-full">
              <ReactMarkdown
                children={currentAssistantMessage}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline ? (
                      <div className="relative">
                        <CopyButton text={String(children).replace(/\n$/, "")} />
                        <SyntaxHighlighter language={match ? match[1] : undefined} PreTag="div" {...props} style={{ overflow: "auto", maxWidth: "100%" }}>
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              />
            </div>
          </div>
        )}
      </div>
      {isLoading && !currentAssistantMessage && <div className="p-4">AI is thinking...</div>}
      {error && <div className="text-red-500 p-4 whitespace-pre-wrap break-words">Error: {error}</div>}
      <form onSubmit={handleSubmit} className="flex p-4 border-t border-gray-300 shrink-0">
        <textarea
          ref={textareaRef}
          className="flex-1 border border-gray-300 rounded-l-md p-2 resize-none overflow-hidden"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            adjustTextareaHeight();
          }}
          onKeyDown={handleKeyDown}
          placeholder="Type your message here... (Shift+Enter for new line)"
          rows={1}
        />
        <button type="submit" className="bg-gray-500 text-white rounded-r-md px-4 py-2" disabled={isLoading}>
          Send
        </button>
      </form>
    </div>
  );
};

export default Chat;
