"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Paper, fetchPapers, deletePaper } from "./PaperApi";

const PapersPage = () => {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [searchId, setSearchId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const router = useRouter();

  useEffect(() => {
    loadPapers();
  }, []);

  const loadPapers = async (id: string = "") => {
    setLoading(true);
    setError("");

    try {
      const data = await fetchPapers(id);
      setPapers(data);
    } catch (error) {
      setError("Failed to fetch papers");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    setLoading(true);
    setError("");

    try {
      await deletePaper(id);
      loadPapers();
    } catch (error) {
      setError("Failed to delete paper");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadPapers(searchId);
  };

  const getTypeString = (type: number) => {
    switch (type) {
      case 1:
        return "Full Paper (全文)";
      case 2:
        return "Short Paper (短文)";
      case 3:
        return "Poster Paper (海报)";
      case 4:
        return "Demo Paper (演示)";
      default:
        return "Unknown Type (未知类型)";
    }
  };

  const getLevelString = (level: number) => {
    switch (level) {
      case 1:
        return "CCF-A";
      case 2:
        return "CCF-B";
      case 3:
        return "CCF-C";
      case 4:
        return "Chinese CCF-A (中文CCF-A)";
      case 5:
        return "Chinese CCF-B (中文CCF-B)";
      case 6:
        return "No Level (无级别)";
      default:
        return "Unknown Level (未知级别)";
    }
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">List of Papers</h1>
      <div className="mb-4">
        <input
          type="text"
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          placeholder="Search by ID"
          className="p-2 border border-gray-300 rounded-md mr-2"
        />
        <button
          onClick={handleSearch}
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
        >
          Search
        </button>
      </div>
      {loading ? (
        <p>Loading...</p>
      ) : error ? (
        <p>{error}</p>
      ) : (
        <ul className="list-disc pl-5">
          {papers.map((paper) => (
            <li key={paper.id} className="mb-4">
              <div className="border p-4 rounded-md shadow-md">
                <strong>ID:</strong> {paper.id}
                <br />
                <strong>Name:</strong> {paper.name}
                <br />
                <strong>Source:</strong> {paper.source}
                <br />
                <strong>Year:</strong> {paper.year}
                <br />
                <strong>Type:</strong> {getTypeString(  paper.type)}
                <br />
                <strong>Level:</strong> {getLevelString(paper.level)}
                <br />
                <em>Authors:</em>
                <ul className="list-disc pl-5">
                  {paper.publishedPapers.map((publishedPaper) => (
                    <li
                      key={`${publishedPaper.paperId}-${publishedPaper.teacherId}`}
                    >
                      Teacher: {publishedPaper.teacher.name} - Ranking:{" "}
                      {publishedPaper.ranking}, Corresponding Author (通讯作者):{" "}
                      {publishedPaper.isCorrespondingAuthor ? "Yes" : "No"}
                    </li>
                  ))}
                </ul>
                <div className="flex space-x-2 mt-2">
                  <button
                    onClick={() => handleDelete(paper.id)}
                    className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
                  >
                    Delete
                  </button>
                  <button
                    onClick={() => router.push(`/papers/edit/${paper.id}`)}
                    className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded"
                  >
                    Edit
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PapersPage;
