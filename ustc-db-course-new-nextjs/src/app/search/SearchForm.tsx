import { useState } from "react";

const SearchForm = ({ onSearch }) => {
  const [teacherId, setTeacherId] = useState("");
  const [startYear, setStartYear] = useState("");
  const [endYear, setEndYear] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(teacherId, startYear, endYear);
  };

  return (
    <form onSubmit={handleSubmit} className="mb-4">
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1" htmlFor="teacherId">
          Teacher ID
        </label>
        <input
          type="text"
          id="teacherId"
          value={teacherId}
          onChange={(e) => setTeacherId(e.target.value)}
          className="w-full border border-gray-300 p-2"
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1" htmlFor="startYear">
          Start Year
        </label>
        <input
          type="text"
          id="startYear"
          value={startYear}
          onChange={(e) => setStartYear(e.target.value)}
          className="w-full border border-gray-300 p-2"
        />
      </div>
      <div className="mb-4">
        <label className="block text-sm font-medium mb-1" htmlFor="endYear">
          End Year
        </label>
        <input
          type="text"
          id="endYear"
          value={endYear}
          onChange={(e) => setEndYear(e.target.value)}
          className="w-full border border-gray-300 p-2"
        />
      </div>
      <button type="submit" className="bg-blue-500 text-white py-2 px-4 rounded">
        Search
      </button>
    </form>
  );
};

export default SearchForm;
