"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Project, fetchProjects, deleteProject } from "./ProjectApi";

const ProjectsPage = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [searchId, setSearchId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const router = useRouter();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async (id: string = "") => {
    setLoading(true);
    setError("");

    try {
      const data = await fetchProjects(id);
      setProjects(data);
    } catch (error) {
      setError("Failed to fetch projects");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    setLoading(true);
    setError("");

    try {
      await deleteProject(id);
      loadProjects();
    } catch (error) {
      setError("Failed to delete project");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadProjects(searchId);
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">List of Projects</h1>
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
          {projects.map((project) => (
            <li key={project.id} className="mb-4">
              <div className="border p-4 rounded-md shadow-md">
                <strong>ID:</strong> {project.id}
                <br />
                <strong>Name:</strong> {project.name}
                <br />
                <strong>Source:</strong> {project.source}
                <br />
                <strong>Project Type:</strong>{" "}
                {(() => {
                  switch (project.projectType) {
                    case 1:
                      return "国家级项目";
                    case 2:
                      return "省部级项目";
                    case 3:
                      return "市厅级项目";
                    case 4:
                      return "企业合作项目";
                    case 5:
                      return "其它类型项目";
                    default:
                      return "未知类型";
                  }
                })()}
                <br />
                <strong>Total Funding:</strong> {project.totalFunding}
                <br />
                <strong>Start Year:</strong> {project.startYear}
                <br />
                <strong>End Year:</strong> {project.endYear}
                <br />
                <em>Participants:</em>
                <ul className="list-disc pl-5">
                  {project.projectParticipants.map((participant) => (
                    <li
                      key={`${participant.projectId}-${participant.teacherId}`}
                    >
                      Teacher: {participant.teacher.name} - Ranking:{" "}
                      {participant.ranking}, Funding: {participant.funding}
                    </li>
                  ))}
                </ul>
                <div className="flex space-x-2 mt-2">
                  <button
                    onClick={() => handleDelete(project.id)}
                    className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
                  >
                    Delete
                  </button>
                  <button
                    onClick={() => router.push(`/projects/edit/${project.id}`)}
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

export default ProjectsPage;
