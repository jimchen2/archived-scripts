export interface Teacher {
    id: string;
    name: string;
    gender: number;
    title: number;
  }
  
  export interface TaughtCourse {
    courseId: string;
    teacherId: string;
    year: number;
    term: number;
    teachingHours: number;
    teacher: Teacher;
  }
  
  export interface Course {
    id: string;
    name: string;
    totalHours: number;
    level: number;
    taughtCourses: TaughtCourse[];
  }
  
  export const fetchCourses = async (id: string = ""): Promise<Course[]> => {
    const response = await fetch(`/api/courses/list${id ? `?id=${id}` : ""}`);
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json();
  };
  
  export const deleteCourse = async (id: string): Promise<void> => {
    const response = await fetch("/api/courses/delete", {
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
  