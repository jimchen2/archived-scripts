import React from "react";

const LevelInput = ({ level, setLevel }) => {
  const handleChange = (e) => {
    const value = parseInt(e.target.value);
    if (value >= 1 && value <= 6) {
      setLevel(value);
    } else {
      alert("请输入1到6之间的级别。");
    }
  };

  return (
    <div className="mb-4">
      <label htmlFor="level" className="block text-gray-700 font-bold mb-2">
        论文级别 (1-CCF-A，2-CCF-B，3-CCF-C，4-中文CCF-A，5-中文CCF-B，6-无级别):
      </label>
      <input
        type="number"
        id="level"
        value={level}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        min="1"
        max="6"
      />
    </div>
  );
};

export default LevelInput;
