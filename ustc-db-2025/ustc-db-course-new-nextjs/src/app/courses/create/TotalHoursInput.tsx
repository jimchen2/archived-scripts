import React from "react";

const TotalHoursInput = ({ totalHours, setTotalHours }) => (
  <div className="mb-4">
    <label htmlFor="totalHours" className="block text-gray-700 font-bold mb-2">
      Total Hours:
    </label>
    <input
      type="number"
      id="totalHours"
      value={totalHours}
      onChange={(e) => setTotalHours(parseInt(e.target.value))}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
    />
  </div>
);

export default TotalHoursInput;
