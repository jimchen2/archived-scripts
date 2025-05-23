import React from "react";

const NameInput = ({ name, setName }) => {
  const handleChange = (e) => {
    setName(e.target.value);
  };

  return (
    <div className="mb-4">
      <label htmlFor="name" className="block text-gray-700 font-bold mb-2">
        Project Name:
      </label>
      <input
        type="text"
        id="name"
        value={name}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        required
      />
    </div>
  );
};

export default NameInput;
