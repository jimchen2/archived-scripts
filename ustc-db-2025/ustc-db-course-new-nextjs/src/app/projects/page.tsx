// components/ProjectsPage.tsx or similar
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Project, fetchProjects, deleteProject } from "./ProjectApi"; // Ensure ProjectApi path is correct

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
    } catch (err) { // Changed error variable name to avoid conflict
      if (err instanceof Error) {
        setError(err.message || "Failed to fetch projects");
      } else {
        setError("An unknown error occurred while fetching projects.");
      }
      setProjects([]); // Clear projects on error
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`Are you sure you want to delete project ${id}?`)) {
      return;
    }
    setLoading(true); // Consider a specific deleting state for the item
    setError("");

    try {
      await deleteProject(id);
      // Reload all projects or filter out the deleted one locally
      setProjects(prevProjects => prevProjects.filter(p => p.id !== id));
      // Optionally, show a success message
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message || "Failed to delete project");
      } else {
        setError("An unknown error occurred while deleting the project.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadProjects(searchId);
  };

  const getProjectTypeName = (type: number) => {
    switch (type) {
      case 1: return "国家级项目";
      case 2: return "省部级项目";
      case 3: return "市厅级项目";
      case 4: return "企业合作项目";
      case 5: return "其它类型项目";
      default: return "未知类型";
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">List of Projects</h1>
      <div className="mb-6 flex items-center space-x-3">
        <input
          type="text"
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          placeholder="Search by ID or Name fragment"
          className="p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 flex-grow"
        />
        <button
          onClick={handleSearch}
          className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-md shadow-sm"
          disabled={loading}
        >
          {loading && searchId ? 'Searching...' : 'Search'}
        </button>
        <button
          onClick={() => { setSearchId(""); loadProjects(); }}
          className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-semibold py-2 px-4 rounded-md shadow-sm"
          disabled={loading && !searchId}
        >
          Clear & Reload All
        </button>
      </div>

      {loading && !projects.length ? ( // Show general loading only if no projects are displayed yet
        <p className="text-center text-gray-600">Loading projects...</p>
      ) : error ? (
        <p className="text-center text-red-600 bg-red-100 p-3 rounded-md">{error}</p>
      ) : projects.length === 0 && !loading ? (
        <p className="text-center text-gray-600">No projects found.</p>
      ) : (
        <ul className="space-y-6">
          {projects.map((project) => (
            <li key={project.id} className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
                <div><strong>ID:</strong> {project.id}</div>
                <div><strong>Name:</strong> {project.name}</div>
                <div><strong>Source:</strong> {project.source || "N/A"}</div>
                <div><strong>Project Type:</strong> {getProjectTypeName(project.projectType)}</div>
                <div><strong>Total Funding:</strong> {project.totalFunding?.toLocaleString() || "N/A"}</div>
                <div><strong>Start Year:</strong> {project.startYear || "N/A"}</div>
                <div><strong>End Year:</strong> {project.endYear || "N/A"}</div>
                {/* Display Project File URL */}
                <div className="md:col-span-2">
                  <strong>Project File:</strong>{" "}
                  {project.projectFileUrl ? (
                    <a
                      href={project.projectFileUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline hover:text-blue-800"
                    >
                      View/Download File
                    </a>
                  ) : (
                    <span className="text-gray-500">No file uploaded</span>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-200">
                <h4 className="font-semibold text-gray-700 mb-2">Participants:</h4>
                {project.projectParticipants && project.projectParticipants.length > 0 ? (
                  <ul className="list-disc pl-5 space-y-1 text-sm text-gray-600">
                    {project.projectParticipants.map((participant) => (
                      <li key={`${participant.projectId}-${participant.teacherId}`}>
                        {participant.teacher.name} (ID: {participant.teacherId}) - Ranking: {participant.ranking}, Funding: {participant.funding?.toLocaleString() || "N/A"}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">No participants listed.</p>
                )}
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => handleDelete(project.id)}
                  className="bg-red-500 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-md shadow-sm text-sm"
                  disabled={loading}
                >
                  Delete
                </button>
                <button
                  onClick={() => router.push(`/projects/edit/${project.id}`)}
                  className="bg-green-500 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-md shadow-sm text-sm"
                >
                  Edit
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ProjectsPage;