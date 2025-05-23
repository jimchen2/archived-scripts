export interface Teacher {
  id: string;
  name: string;
  gender: number;
  title: number;
}

export interface ProjectParticipant {
  projectId: string;
  teacherId: string;
  ranking: number;
  funding?: number | null; // Matches Prisma schema (Float?)
  teacher: Teacher;
}

export interface Project {
  id: string;
  name: string;
  source?: string | null; // Matches Prisma schema (String?)
  projectType: number;
  totalFunding?: number | null; // Matches Prisma schema (Float?)
  startYear?: number | null; // Matches Prisma schema (Int?)
  endYear?: number | null; // Matches Prisma schema (Int?)
  projectFileUrl?: string | null; // <<< ADDED THIS FIELD, optional
  projectParticipants: ProjectParticipant[];
}

// Your existing fetchProjects and deleteProject functions remain the same
export const fetchProjects = async (id: string = ""): Promise<Project[]> => {
  const response = await fetch(`/api/projects/list${id ? `?id=${id}` : ""}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: "Network response was not ok" }));
    throw new Error(errorData.error || "Failed to fetch projects");
  }
  return response.json();
};

export const deleteProject = async (id: string): Promise<void> => {
  const response = await fetch("/api/projects/delete", {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: "Network response was not ok" }));
    throw new Error(errorData.error || "Failed to delete project");
  }
};
