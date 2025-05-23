import React from "react";

const ProjectTypeInput = ({ projectType, setProjectType }) => {
  const handleChange = (e) => {
    setProjectType(parseInt(e.target.value));
  };

  return (
    <div className="mb-4">
      <label htmlFor="projectType" className="block text-gray-700 font-bold mb-2">
        项目类型:
      </label>
      <select
        id="projectType"
        value={projectType}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        required
      >
        <option value="">选择项目类型</option>
        <option value={1}>国家级项目</option>
        <option value={2}>省部级项目</option>
        <option value={3}>市厅级项目</option>
        <option value={4}>企业合作项目</option>
        <option value={5}>其它类型项目</option>
      </select>
    </div>
  );
};

export default ProjectTypeInput;
