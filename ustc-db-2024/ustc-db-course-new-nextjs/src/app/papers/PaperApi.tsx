export interface Teacher {
  id: string;
  name: string;
  gender: number;
  title: number;
}

export interface PublishedPaper {
  paperId: number;
  teacherId: string;
  ranking: number;
  isCorrespondingAuthor: boolean;
  teacher: Teacher;
}

export interface Paper {
  id: number;
  name: string;
  source: string;
  year: number;
  type: number;
  level: number;
  publishedPapers: PublishedPaper[];
}

export const fetchPapers = async (id: string = ""): Promise<Paper[]> => {
  const response = await fetch(`/api/papers/list${id ? `?id=${id}` : ""}`);
  if (!response.ok) {
    throw new Error("Network response was not ok");
  }
  return response.json();
};

export const deletePaper = async (id: number): Promise<void> => {
  const response = await fetch("/api/papers/delete", {
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
