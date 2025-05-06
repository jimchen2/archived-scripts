import React from "react";

const YearInput = ({ label, year, setYear }) => {
  const handleChange = (e) => {
    setYear(parseInt(e.target.value));
  };

  return (
    <div className="mb-4">
      <label htmlFor="year" className="block text-gray-700 font-bold mb-2">
        {label}:
      </label>
      <input
        type="number"
        id="year"
        value={year}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        required
    />
    </div>
  );
};

export default YearInput;
