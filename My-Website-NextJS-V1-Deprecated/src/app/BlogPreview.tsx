"use client";
import React, { useEffect, useState } from "react";
import { ChevronDownIcon } from "@heroicons/react/solid";

interface DocumentEntry {
  title: string;
  date: string;
  access: 1 | 2 | 3;
}

interface DocumentType {
  type: string;
  documents: DocumentEntry[];
}

interface BlogPreviewProps {
  mobile: boolean;
  newlines?: number;
  fontSize?: string;
  onSelectBlogId: (title: string) => void;
}

const BlogPreview: React.FC<BlogPreviewProps> = ({ 
  mobile, 
  newlines = 4, 
  fontSize = "text-2xl", 
  onSelectBlogId 
}) => {
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [openDropdowns, setOpenDropdowns] = useState<{ [key: string]: boolean }>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const res = await fetch("/api/previewBlog");
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data: DocumentType[] = await res.json();
        setDocumentTypes(data);
      } catch (error) {
        console.error("Failed to fetch documents:", error);
        setError("Failed to load documents. Please try again later.");
      }
    };

    fetchDocuments();
  }, []);

  const toggleDropdown = (type: string) => {
    setOpenDropdowns((prevOpenDropdowns) => ({
      ...prevOpenDropdowns,
      [type]: !prevOpenDropdowns[type],
    }));
  };

  const handleSelectDocument = (title: string) => {
    onSelectBlogId(title);
    if (mobile) {
      window.scrollTo({ top: 0, behavior: "auto" });
    }
  };

  const renderNewlines = () => {
    return Array.from({ length: newlines }).map((_, idx) => <br key={idx} />);
  };

  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 font-opensans">
      <div className="w-full sticky top-0">
        {renderNewlines()}
        <header className={`${fontSize} font-normal p-4 text-center`}>
          My Blogs
        </header>
        <ul className="overflow-x-hidden">
          {documentTypes.map((docType) => (
            <li key={docType.type}>
              <div className="rounded-lg transition duration-300 ease-in-out transform">
                <div
                  className={`flex items-center space-y-2 text-sm cursor-pointer justify-between hover:bg-gray-200 p-3 ${
                    mobile ? "min-w-[320px]" : ""
                  }`}
                  onClick={() => toggleDropdown(docType.type)}
                >
                  <h4 className="font-medium text-gray-800">
                    {docType.type} ({docType.documents.length})
                  </h4>
                  <ChevronDownIcon
                    className={`h-5 w-5 text-gray-800 duration-300 ease-in-out ${
                      openDropdowns[docType.type] ? "rotate-180" : "rotate-0"
                    }`}
                  />
                </div>
                <div
                  className={`transition-max-height duration-500 ease-in-out overflow-auto ${
                    openDropdowns[docType.type]
                      ? "max-h-[500px] opacity-100"
                      : "max-h-0 opacity-0"
                  }`}
                >
                  <ul className="mt-2 space-y-2">
                    {docType.documents.map((doc) => (
                      <li
                        key={doc.title}
                        className="p-2 rounded-lg transition duration-300 ease-in-out transform text-xs hover:bg-gray-200 hover:shadow-lg hover:cursor-pointer"
                        onClick={() => handleSelectDocument(doc.title)}
                      >
                        <div className="flex justify-center">
                          <h6 className="text-center text-sm font-normal">
                            {doc.title}
                          </h6>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </li>
          ))}
          {renderNewlines()}
        </ul>
      </div>
    </div>
  );
};

BlogPreview.displayName = 'BlogPreview';

export default BlogPreview;