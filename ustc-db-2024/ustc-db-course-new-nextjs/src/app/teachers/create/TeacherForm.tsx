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
        <label htmlFor="id" className="block text-gray-700 font-bold mb-2">
          ID:
        </label>
        <input
          type="text"
          id="id"
          name="id"
          value={formData.id}
          onChange={handleChange}
          required
          maxLength={5}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-sm text-gray-500">最多 5 个字符</p>
      </div>
      <div className="mb-4">
        <label htmlFor="name" className="block text-gray-700 font-bold mb-2">
          姓名:
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          maxLength={256}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-sm text-gray-500">最多 256 个字符</p>
      </div>
      <div className="mb-4">
        <label htmlFor="gender" className="block text-gray-700 font-bold mb-2">
          性别:
        </label>
        <select
          id="gender"
          name="gender"
          value={formData.gender}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">选择性别</option>
          <option value="1">男</option>
          <option value="2">女</option>
          <option value="3">其他</option>
        </select>
      </div>
      <div className="mb-4">
        <label htmlFor="title" className="block text-gray-700 font-bold mb-2">
          职称:
        </label>
        <select
          id="title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
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
        className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
      >
        创建教师
      </button>
    </form>
  );
};

export default TeacherForm;
