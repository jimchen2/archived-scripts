import React from "react";

const YearInput = ({ year, setYear }) => (
  <div className="mb-4">
    <label htmlFor="year" className="block text-gray-700 font-bold mb-2">
      Year:
    </label>
    <input
      type="number"
      id="year"
      value={year}
      onChange={(e) => setYear(parseInt(e.target.value))}
      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
    />
  </div>
);

export default YearInput;
