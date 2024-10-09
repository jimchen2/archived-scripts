"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import NameInput from "../../create/NameInput";
import SourceInput from "../../create/SourceInput";
import ProjectTypeInput from "../../create/ProjectTypeInput";
import FundingInput from "../../create/FundingInput";
import YearInput from "../../create/YearInput";
import ProjectParticipantsInput from "../../create/ProjectParticipantsInput";

interface PageProps {
  params: {
    id: string;
  };
}

const EditProjectPage = ({ params }: PageProps) => {
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
  const { id: projectId } = params;

  useEffect(() => {
    const fetchProjectData = async () => {
      try {
        const res = await fetch(`/api/projects/list/?id=${projectId}`);
        if (res.ok) {
          const data = await res.json();
          const project = data[0]; // Assuming the response is an array with a single project object
          setName(project.name);
          setSource(project.source);
          setProjectType(project.projectType);
          setTotalFunding(project.totalFunding);
          setStartYear(project.startYear);
          setEndYear(project.endYear);
          setProjectParticipants(
            project.projectParticipants.reduce((acc, pp, index) => {
              acc[`participant_${index}`] = pp;
              return acc;
            }, {})
          );
        } else {
          setErrorMessage("Error fetching project data.");
        }
      } catch (error) {
        setErrorMessage("An error occurred while fetching the project data.");
      }
    };

    if (projectId) {
      fetchProjectData();
    }
  }, [projectId]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const projectData = {
      id: projectId,
      name,
      source,
      projectType,
      totalFunding,
      startYear,
      endYear,
      projectParticipants,
    };

    try {
      const res = await fetch(`/api/projects/edit`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(projectData),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessMessage("Project updated successfully!");
        setTimeout(() => {
          router.push("/projects");
        }, 2000);
      } else {
        const errorData = await res.json();
        setErrorMessage(errorData.error || "Error updating project");
      }
    } catch (error) {
      setErrorMessage("An error occurred while updating the project.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-sm">
      <NameInput name={name} setName={setName} />
      <SourceInput source={source} setSource={setSource} />
      <ProjectTypeInput projectType={projectType} setProjectType={setProjectType} />
      <FundingInput totalFunding={totalFunding} setTotalFunding={setTotalFunding} />
      <YearInput label="Start Year" year={startYear} setYear={setStartYear} />
      <YearInput label="End Year" year={endYear} setYear={setEndYear} />
      <ProjectParticipantsInput
        projectParticipants={projectParticipants}
        setProjectParticipants={setProjectParticipants}
      />
      <button
        type="submit"
        className="px-4 py-2 bg-green-500 text-white rounded-md"
      >
        Update Project
      </button>
      {errorMessage && <p className="text-red-500 mt-4">{errorMessage}</p>}
      {successMessage && (
        <p className="text-green-500 mt-4">{successMessage}</p>
      )}
    </form>
  );
};

export default EditProjectPage;
