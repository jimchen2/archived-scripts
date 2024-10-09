import React from "react";

const SourceInput = ({ source, setSource }) => (
  <div className="mb-4">
    <label htmlFor="source" className="block text-gray-700 font-bold mb-2">
      Source:
    </label>
    <input
      type="text"
      id="source"
      value={source}
      onChange={(e) => setSource(e.target.value)}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
    />
  </div>
);

export default SourceInput;
