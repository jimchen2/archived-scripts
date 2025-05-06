"use client";

import React, { useState } from "react";
import IdInput from "./IdInput";
import NameInput from "./NameInput";
import SourceInput from "./SourceInput";
import ProjectTypeInput from "./ProjectTypeInput";
import FundingInput from "./FundingInput";
import YearInput from "./YearInput";
import ProjectParticipantsInput from "./ProjectParticipantsInput";
import { useRouter } from "next/navigation";

const CreateProjectPage = () => {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [source, setSource] = useState("");
  const [projectType, setProjectType] = useState(1);
  const [totalFunding, setTotalFunding] = useState(0);
  const [startYear, setStartYear] = useState(new Date().getFullYear());
  const [endYear, setEndYear] = useState(new Date().getFullYear());
  const [projectParticipants, setProjectParticipants] = useState({});
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();

    const projectData = { id, name, source, projectType, totalFunding, startYear, endYear, projectParticipants };

    try {
      const res = await fetch("/api/projects/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(projectData),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessMessage("Project created successfully!");
        setTimeout(() => {
          router.push("/projects");
        }, 2000);
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Error creating project");
      }
    } catch (error) {
      setErrorMessage("An error occurred while creating the project.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-sm">
      <IdInput id={id} setId={setId} />
      <NameInput name={name} setName={setName} />
      <SourceInput source={source} setSource={setSource} />
      <ProjectTypeInput projectType={projectType} setProjectType={setProjectType} />
      <FundingInput totalFunding={totalFunding} setTotalFunding={setTotalFunding} />
      <YearInput label="Start Year" year={startYear} setYear={setStartYear} />
      <YearInput label="End Year" year={endYear} setYear={setEndYear} />
      <ProjectParticipantsInput projectParticipants={projectParticipants} setProjectParticipants={setProjectParticipants} />
      <button type="submit" className="px-4 py-2 bg-green-500 text-white rounded-md">
        Create Project
      </button>
      {errorMessage && <p className="text-red-500 mt-4">{errorMessage}</p>}
      {successMessage && <p className="text-green-500 mt-4">{successMessage}</p>}
    </form>
  );
};

export default CreateProjectPage;
