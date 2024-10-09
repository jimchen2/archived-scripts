import React from "react";

interface TeacherFormProps {
  formData: {
    id: string;
    name: string;
    gender: string;
    title: string;
  };
  handleChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => void;
  handleSubmit: (e: React.FormEvent) => void;
}

const TeacherForm: React.FC<TeacherFormProps> = ({
  formData,
  handleChange,
  handleSubmit,
}) => {
  return (
    <form onSubmit={handleSubmit} className="max-w-sm">
      <div className="mb-4">
        <label htmlFor="name" className="block mb-2">
          姓名:
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded"
        />
      </div>
      <div className="mb-4">
        <label htmlFor="gender" className="block mb-2">
          性别:
        </label>
        <select
          id="gender"
          name="gender"
          value={formData.gender}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded"
        >
          <option value="">选择性别</option>
          <option value="1">男</option>
          <option value="2">女</option>
          <option value="3">其他</option>
        </select>
      </div>
      <div className="mb-4">
        <label htmlFor="title" className="block mb-2">
          职称:
        </label>
        <select
          id="title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded"
        >
          <option value="">选择职称</option>
          <option value="1">博士后</option>
          <option value="2">助教</option>
          <option value="3">讲师</option>
          <option value="4">副教授</option>
          <option value="5">特任教授</option>
          <option value="6">教授</option>
          <option value="7">助理研究员</option>
          <option value="8">特任副研究员</option>
          <option value="9">副研究员</option>
          <option value="10">特任研究员</option>
          <option value="11">研究员</option>
        </select>
      </div>
      <button
        type="submit"
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        更新
      </button>
    </form>
  );
};

export default TeacherForm;
