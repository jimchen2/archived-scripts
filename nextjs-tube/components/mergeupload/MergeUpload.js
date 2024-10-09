import React, { useState } from "react";
import TagInput from "../fileupload/TagInput";
import LanguageSelector from "../fileupload/LanguageSelector";

const MergeUpload = () => {
  const [uploadData, setUploadData] = useState({
    platform: 'youtube',
    externalUrl: '',
    language: 'en-US',
    filename: '',
    tags: [],
  });
  const [urlError, setUrlError] = useState('');
  const [filenameError, setFilenameError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUploadData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
    if (name === 'externalUrl') {
      setUrlError('');
    }
    if (name === 'filename') {
      setFilenameError('');
    }
  };

  const handleTagsChange = (tags) => {
    setUploadData((prevData) => ({
      ...prevData,
      tags: tags,
    }));
  };

  const handleLanguageChange = (language) => {
    setUploadData((prevData) => ({
      ...prevData,
      language: language,
    }));
  };

  const isValidYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;
    return youtubeRegex.test(url);
  };

  const handleUpload = async () => {
    if (!isValidYouTubeUrl(uploadData.externalUrl)) {
      setUrlError('Please enter a valid YouTube URL');
      return;
    }
    if (!uploadData.filename.trim()) {
      setFilenameError('Filename is required');
      return;
    }
  
    try {
      const formData = new FormData();
      Object.keys(uploadData).forEach(key => {
        if (key === 'tags') {
          formData.append(key, JSON.stringify(uploadData[key]));
        } else {
          formData.append(key, uploadData[key]);
        }
      });

      const response = await fetch("/api/merge/merge-videos", {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        console.log("Merge successful:", data);
        // Handle success (e.g., show success message, clear form)
      } else {
        console.error("Merge failed:", data.message);
        // Handle error (e.g., show error message to user)
      }
    } catch (error) {
      console.error("Merge failed:", error);
      // Handle network errors
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-4">Merge Video</h2>
      <div className="mb-4">
        <label className="block text-md font-medium mb-2">Platform</label>
        <select
          name="platform"
          value={uploadData.platform}
          onChange={handleChange}
          className="p-2 border rounded w-full mb-2"
          disabled
        >
          <option value="youtube">YouTube</option>
        </select>
      </div>
      <div className="mb-4">
        <label className="block text-md font-medium mb-2">YouTube URL</label>
        <input
          type="text"
          name="externalUrl"
          placeholder="Enter YouTube URL"
          value={uploadData.externalUrl}
          onChange={handleChange}
          className={`p-2 border rounded w-full mb-2 ${urlError ? 'border-red-500' : ''}`}
          required
        />
        {urlError && <p className="text-red-500 text-sm">{urlError}</p>}
      </div>
      <div className="mb-4">
        <label className="block text-md font-medium mb-2">Filename</label>
        <input
          type="text"
          name="filename"
          placeholder="Enter filename"
          value={uploadData.filename}
          onChange={handleChange}
          className={`p-2 border rounded w-full mb-2 ${filenameError ? 'border-red-500' : ''}`}
          required
        />
        {filenameError && <p className="text-red-500 text-sm">{filenameError}</p>}
      </div>
      <LanguageSelector
        language={uploadData.language}
        setLanguage={handleLanguageChange}
      />
      <TagInput tags={uploadData.tags} setTags={handleTagsChange} />
      <button
        onClick={handleUpload}
        className="p-2 text-md w-full bg-blue-500 text-white rounded-lg hover:bg-blue-600"
      >
        Merge Video
      </button>
    </div>
  );
};

export default MergeUpload;