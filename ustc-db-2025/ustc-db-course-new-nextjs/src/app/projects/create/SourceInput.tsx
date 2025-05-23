import React from "react";

const SourceInput = ({ source, setSource }) => {
  const handleChange = (e) => {
    setSource(e.target.value);
  };

  return (
    <div className="mb-4">
      <label htmlFor="source" className="block text-gray-700 font-bold mb-2">
        Source:
      </label>
      <input
        type="text"
        id="source"
        value={source}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        required
    />
    </div>
  );
};

export default SourceInput;
