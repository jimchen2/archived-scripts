import React from "react";

const FileInput = ({ handleFileChange }) => {
  return (
    <input
      type="file"
      accept="video/*"
      onChange={handleFileChange}
      className="w-full text-md text-gray-900 cursor-pointer mb-4"
    />
  );
};

export default FileInput;
