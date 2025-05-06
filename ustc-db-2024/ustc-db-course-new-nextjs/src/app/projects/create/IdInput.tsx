import React from "react";

const IdInput = ({ id, setId }) => {
  const handleChange = (e) => {
    setId(e.target.value);
  };

  return (
    <div className="mb-4">
      <label htmlFor="id" className="block text-gray-700 font-bold mb-2">
        Project ID:
      </label>
      <input
        type="text"
        id="id"
        value={id}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        required
      />
    </div>
  );
};

export default IdInput;
