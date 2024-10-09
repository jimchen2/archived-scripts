"use client";

import React, { useState } from "react";
import NameInput from "./NameInput";
import SourceInput from "./SourceInput";
import YearInput from "./YearInput";
import TypeInput from "./TypeInput";
import LevelInput from "./LevelInput";
import PublishedPapersInput from "./PublishedPapersInput";
import { useRouter } from "next/navigation";

const CreatePaperPage = () => {
  const [name, setName] = useState("");
  const [source, setSource] = useState("");
  const [year, setYear] = useState(new Date().getFullYear());
  const [type, setType] = useState(1);
  const [level, setLevel] = useState(1);
  const [publishedPapers, setPublishedPapers] = useState({});
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();

    const paperData = { name, source, year, type, level, publishedPapers };

    try {
      const res = await fetch("/api/papers/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(paperData),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessMessage("Paper created successfully!");
        setTimeout(() => {
          router.push("/papers");
        }, 2000);
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Error creating paper");
      }
    } catch (error) {
      setErrorMessage("An error occurred while creating the paper.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-sm">
      <NameInput name={name} setName={setName} />
      <SourceInput source={source} setSource={setSource} />
      <YearInput year={year} setYear={setYear} />
      <TypeInput type={type} setType={setType} />
      <LevelInput level={level} setLevel={setLevel} />
      <PublishedPapersInput publishedPapers={publishedPapers} setPublishedPapers={setPublishedPapers} />
      <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded-md">
        Create Paper
      </button>
      {errorMessage && <p className="text-red-500 mt-4">{errorMessage}</p>}
      {successMessage && <p className="text-green-500 mt-4">{successMessage}</p>}
    </form>
  );
};

export default CreatePaperPage;
