import React from "react";

const ProgressBar = ({ file, uploadProgress, uploadedSize }) => {
  const totalSize = file ? file.size : 0;

  return (
    file && (
      <div className="mt-4 w-full rounded-lg">
        <div className="text-xs mt-2">
          Uploaded {uploadedSize} of {totalSize} bytes
        </div>
      </div>
    )
  );
};

export default ProgressBar;
