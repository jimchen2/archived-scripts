"use client";

import { useState, ChangeEvent, FormEvent } from "react";
import { useRouter } from "next/navigation";
import TeacherForm from "./TeacherForm";

const CreateTeacher = () => {
  const [formData, setFormData] = useState({
    id: "",
    name: "",
    gender: "",
    title: "",
  });
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null); // Reset error state
    try {
      const response = await fetch("/api/teachers/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        router.push("/teachers");
      } else {
        const data = await response.json();
        setError(data.error || "创建教师失败");
      }
    } catch (error) {
      console.error("Error creating teacher:", error);
      setError("创建教师失败");
    }
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">创建教师</h1>
      {error && <p className="text-red-500 mb-4">{error}</p>}
      <TeacherForm
        formData={formData}
        handleChange={handleChange}
        handleSubmit={handleSubmit}
      />
    </div>
  );
};

export default CreateTeacher;
