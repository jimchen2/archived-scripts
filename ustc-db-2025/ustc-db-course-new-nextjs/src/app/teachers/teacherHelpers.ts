export interface Teacher {
  id: string;
  name: string;
  gender: number;
  title: number;
}

export const fetchTeachers = async (
  setTeachers: React.Dispatch<React.SetStateAction<Teacher[]>>,
  id?: string
) => {
  try {
    const response = await fetch(`/api/teachers/list${id ? `?id=${id}` : ""}`);
    const data = await response.json();
    setTeachers(data);
  } catch (error) {
    console.error("Error fetching teachers:", error);
  }
};

export const handleDelete = async (
  id: string,
  setTeachers: React.Dispatch<React.SetStateAction<Teacher[]>>
) => {
  try {
    await fetch(`/api/teachers/delete`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ id }),
    });
    fetchTeachers(setTeachers); // Refresh the list after deletion
  } catch (error) {
    console.error("Error deleting teacher:", error);
  }
};

export const getGender = (gender: number): string => {
  switch (gender) {
    case 1:
      return "男";
    case 2:
      return "女";
    case 3:
      return "其他";
    default:
      return "未知";
  }
};

export const getTitle = (title: number): string => {
  switch (title) {
    case 1:
      return "博士后";
    case 2:
      return "助教";
    case 3:
      return "讲师";
    case 4:
      return "副教授";
    case 5:
      return "特任教授";
    case 6:
      return "教授";
    case 7:
      return "助理研究员";
    case 8:
      return "特任副研究员";
    case 9:
      return "副研究员";
    case 10:
      return "特任研究员";
    case 11:
      return "研究员";
    default:
      return "未知职称";
  }
};
