import React from "react";

const IdInput = ({ id, setId }) => (
  <div className="mb-4">
    <label htmlFor="id" className="block text-gray-700 font-bold mb-2">
      ID:
    </label>
    <input
      type="text"
      id="id"
      value={id}
      onChange={(e) => setId(e.target.value)}
      required
      maxLength={5}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
    />
    <p className="text-sm text-gray-500">最多 5 个字符</p>
  </div>
);

export default IdInput;
