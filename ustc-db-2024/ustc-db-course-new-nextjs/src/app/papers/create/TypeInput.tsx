import React from "react";

const TypeInput = ({ type, setType }) => {
  const handleChange = (e) => {
    const value = parseInt(e.target.value);
    if (value >= 1 && value <= 4) {
      setType(value);
    } else {
      alert("请输入1到4之间的类型。");
    }
  };

  return (
    <div className="mb-4">
      <label htmlFor="type" className="block text-gray-700 font-bold mb-2">
        论文类型 (1-全文，2-短文，3-海报，4-演示):
      </label>
      <input
        type="number"
        id="type"
        value={type}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        min="1"
        max="4"
      />
    </div>
  );
};

export default TypeInput;
