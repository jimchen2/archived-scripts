import React from "react";

const LevelInput = ({ level, setLevel }) => (
  <div className="mb-4">
    <label htmlFor="level" className="block text-gray-700 font-bold mb-2">
      Level:
    </label>
    <input
      type="number"
      id="level"
      value={level}
      onChange={(e) => setLevel(parseInt(e.target.value))}
      required
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
      min="1"
      max="2"
    />
    <p className="text-sm text-gray-500">1 - 本科生课程, 2 - 研究生课程</p>
  </div>
);

export default LevelInput;
