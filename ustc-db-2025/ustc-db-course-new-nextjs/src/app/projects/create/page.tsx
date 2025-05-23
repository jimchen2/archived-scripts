// components/CreateProjectPage.js
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
  const [file, setFile] = useState(null); // New state for the selected file
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false); // To prevent double submissions
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");
    setIsSubmitting(true); // Disable button during submission

    let projectFileUrl = null;

    // --- File Upload Logic ---
    if (file) {
      try {
        const formData = new FormData();
        formData.append("file", file);

        // Send the file to your Next.js API route for upload to R2
        const uploadRes = await fetch("/api/projects/upload", {
          method: "POST",
          body: formData, // No 'Content-Type' header needed for FormData, browser sets it.
        });

        if (!uploadRes.ok) {
          const errorData = await uploadRes.json();
          throw new Error(errorData.error || "File upload failed.");
        }

        const uploadResult = await uploadRes.json();
        projectFileUrl = uploadResult.fileUrl; // Get the public URL of the uploaded file
        setSuccessMessage("File uploaded successfully! Creating project...");
      } catch (uploadError) {
        console.error("File upload error:", uploadError);
        setErrorMessage(uploadError.message);
        setIsSubmitting(false); // Re-enable button on error
        return; // Stop execution if file upload fails
      }
    }
    // --- End File Upload Logic ---

    const projectData = {
      id,
      name,
      source,
      projectType,
      totalFunding,
      startYear,
      endYear,
      projectParticipants,
      projectFileUrl, // Include the file URL in your project data
    };

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
        setErrorMessage(errorData.error || "Error creating project.");
      }
    } catch (error) {
      console.error("Project creation error:", error);
      setErrorMessage("An error occurred while creating the project: " + error.message);
    } finally {
      setIsSubmitting(false); // Always re-enable button
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-sm mx-auto p-4 bg-white shadow-md rounded-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Create New Project</h2>

      <IdInput id={id} setId={setId} />
      <NameInput name={name} setName={setName} />
      <SourceInput source={source} setSource={setSource} />
      <ProjectTypeInput projectType={projectType} setProjectType={setProjectType} />
      <FundingInput totalFunding={totalFunding} setTotalFunding={setTotalFunding} />
      <YearInput label="Start Year" year={startYear} setYear={setStartYear} />
      <YearInput label="End Year" year={endYear} setYear={setEndYear} />
      <ProjectParticipantsInput projectParticipants={projectParticipants} setProjectParticipants={setProjectParticipants} />

      {/* New File Upload Input */}
      <div className="mb-4">
        <label htmlFor="projectFile" className="block text-gray-700 text-sm font-bold mb-2">
          Project File (Optional)
        </label>
        <input
          type="file"
          id="projectFile"
          className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
        />
        {file && <p className="text-sm text-gray-600 mt-1">Selected file: {file.name}</p>}
      </div>

      <button
        type="submit"
        className="px-4 py-2 bg-green-600 text-white font-semibold rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={isSubmitting}
      >
        {isSubmitting ? "Creating..." : "Create Project"}
      </button>

      {errorMessage && <p className="text-red-600 mt-4 text-sm">{errorMessage}</p>}
      {successMessage && <p className="text-green-600 mt-4 text-sm">{successMessage}</p>}
    </form>
  );
};

export default CreateProjectPage;