"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import NameInput from "../../create/NameInput";
import SourceInput from "../../create/SourceInput";
import YearInput from "../../create/YearInput";
import TypeInput from "../../create/TypeInput";
import LevelInput from "../../create/LevelInput";
import PublishedPapersInput from "../../create/PublishedPapersInput";

interface PageProps {
  params: {
    id: string;
  };
}

const EditPaperPage = ({ params }: PageProps) => {
  const [name, setName] = useState("");
  const [source, setSource] = useState("");
  const [year, setYear] = useState(new Date().getFullYear());
  const [type, setType] = useState(1);
  const [level, setLevel] = useState(1);
  const [publishedPapers, setPublishedPapers] = useState({});
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const router = useRouter();
  const { id: paperId } = params;

  useEffect(() => {
    const fetchPaperData = async () => {
      try {
        const res = await fetch(`/api/papers/list/?id=${paperId}`);
        if (res.ok) {
          const data = await res.json();
          const paper = data[0]; // Assuming the response is an array with a single paper object
          setName(paper.name);
          setSource(paper.source);
          setYear(paper.year);
          setType(paper.type);
          setLevel(paper.level);
          setPublishedPapers(
            paper.publishedPapers.reduce((acc, pp, index) => {
              acc[`published_${index}`] = pp;
              return acc;
            }, {})
          );
        } else {
          setErrorMessage("Error fetching paper data.");
        }
      } catch (error) {
        setErrorMessage("An error occurred while fetching the paper data.");
      }
    };

    if (paperId) {
      fetchPaperData();
    }
  }, [paperId]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const paperData = {
      id: parseInt(paperId),
      name,
      source,
      year,
      type,
      level,
      publishedPapers,
    };

    try {
      const res = await fetch(`/api/papers/edit`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(paperData),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessMessage("Paper updated successfully!");
        setTimeout(() => {
          router.push("/papers");
        }, 2000);
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Error updating paper");
      }
    } catch (error) {
      setErrorMessage("An error occurred while updating the paper.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-sm">
      <NameInput name={name} setName={setName} />
      <SourceInput source={source} setSource={setSource} />
      <YearInput year={year} setYear={setYear} />
      <TypeInput type={type} setType={setType} />
      <LevelInput level={level} setLevel={setLevel} />
      <PublishedPapersInput
        publishedPapers={publishedPapers}
        setPublishedPapers={setPublishedPapers}
      />
      <button
        type="submit"
        className="px-4 py-2 bg-green-500 text-white rounded-md"
      >
        Update Paper
      </button>
      {errorMessage && <p className="text-red-500 mt-4">{errorMessage}</p>}
      {successMessage && (
        <p className="text-green-500 mt-4">{successMessage}</p>
      )}
    </form>
  );
};

export default EditPaperPage;
