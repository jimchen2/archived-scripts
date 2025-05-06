"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import TeacherForm from "./TeacherForm";

interface Teacher {
  id: string;
  name: string;
  gender: number;
  title: number;
}

interface PageProps {
  params: {
    id: string;
  };
}

const EditTeacherPage = ({ params }: PageProps) => {
  const [teacher, setTeacher] = useState<Teacher | null>(null);
  const [formData, setFormData] = useState({
    id: "",
    name: "",
    gender: "",
    title: "",
  });
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();
  const { id } = params;

  useEffect(() => {
    fetchTeacher(id);
  }, [id]);

  const fetchTeacher = async (id: string) => {
    try {
      const response = await fetch(`/api/teachers/list?id=${id}`);
      const data = await response.json();
      if (data.length > 0) {
        const teacherData = data[0];
        setTeacher(teacherData);
        setFormData({
          id: teacherData.id,
          name: teacherData.name,
          gender: teacherData.gender.toString(),
          title: teacherData.title.toString(),
        });
      }
    } catch (error) {
      console.error("Error fetching teacher:", error);
      setError("获取教师信息失败");
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!id || !formData.name || !formData.gender || !formData.title) {
      setError("表单数据无效");
      return;
    }

    try {
      const response = await fetch(`/api/teachers/edit`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id: formData.id,
          name: formData.name,
          gender: parseInt(formData.gender),
          title: parseInt(formData.title),
        }),
      });

      if (response.ok) {
        router.push("/teachers");
      } else {
        const data = await response.json();
        setError(data.error || "更新教师信息失败");
      }
    } catch (error) {
      console.error("Error updating teacher:", error);
      setError("更新教师信息失败");
    }
  };

  if (!teacher) {
    return <div>加载中...</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">编辑教师</h1>
      {error && <p className="text-red-500 mb-4">{error}</p>}
      <TeacherForm
        formData={formData}
        handleChange={handleChange}
        handleSubmit={handleSubmit}
      />
    </div>
  );
};

export default EditTeacherPage;
