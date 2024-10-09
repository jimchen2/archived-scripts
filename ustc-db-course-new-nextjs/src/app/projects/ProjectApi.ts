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
    funding: number;
    teacher: Teacher;
  }
  
  export interface Project {
    id: string;
    name: string;
    source: string;
    projectType: number;
    totalFunding: number;
    startYear: number;
    endYear: number;
    projectParticipants: ProjectParticipant[];
  }
  
  export const fetchProjects = async (id: string = ""): Promise<Project[]> => {
    const response = await fetch(`/api/projects/list${id ? `?id=${id}` : ""}`);
    if (!response.ok) {
      throw new Error("Network response was not ok");
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
      throw new Error("Network response was not ok");
    }
  };
  