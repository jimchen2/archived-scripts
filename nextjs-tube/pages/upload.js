import { useState } from "react";
import FileUpload from "../components/fileupload/FileUpload";
import MergeIndex from "../components/mergeupload/MergeUpload";

const Upload = () => {
  const [uploadType, setUploadType] = useState("file");

  const toggleUploadType = () => {
    setUploadType(uploadType === "file" ? "merge" : "file");
  };

  return (
    <div className="container mx-auto mt-10 grayscale max-w-[600px]">
      <h2 className="text-2xl mb-6 text-center">Choose Upload Type</h2>
      <div className="mb-4 text-center">
        <button
          onClick={toggleUploadType}
          className="p-2 text-md ring-1 hover:bg-gray-200 text-gray-800 rounded-lg"
        >
          Switch to {uploadType === "file" ? "Merge Index" : "File Upload"} 
        </button>
      </div>
      <br/>
      <br/>
      <br/>
      <div className="w-full">
        {uploadType === "file" ? (
          <div>
            <FileUpload />
          </div>
        ) : (
          <div>
            <MergeIndex />
          </div>
        )}
      </div>
    </div>
  );
};

export default Upload;