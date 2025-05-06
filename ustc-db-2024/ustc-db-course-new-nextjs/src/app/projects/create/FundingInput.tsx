import React from "react";

const FundingInput = ({ totalFunding, setTotalFunding }) => {
  const handleChange = (e) => {
    setTotalFunding(parseFloat(e.target.value));
  };

  return (
    <div className="mb-4">
      <label htmlFor="totalFunding" className="block text-gray-700 font-bold mb-2">
        Total Funding:
      </label>
      <input
        type="number"
        id="totalFunding"
        value={totalFunding}
        required
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
      />
    </div>
  );
};

export default FundingInput;
