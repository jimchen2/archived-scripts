import React from "react";

const PublishedPapersInput = ({ publishedPapers, setPublishedPapers }) => {
  const handleAddPaper = () => {
    const newKey = `paper_${Date.now()}`;
    setPublishedPapers({ ...publishedPapers, [newKey]: { teacherId: "", ranking: 1, isCorrespondingAuthor: false } });
  };

  const handleDeletePaper = (key) => {
    const newPublishedPapers = { ...publishedPapers };
    delete newPublishedPapers[key];
    setPublishedPapers(newPublishedPapers);
  };

  const handlePaperChange = (key, field, value) => {
    setPublishedPapers({
      ...publishedPapers,
      [key]: { ...publishedPapers[key], [field]: value },
    });
  };

  return (
    <div className="mb-4">
      <label className="block text-gray-700 font-bold mb-2">Authors:</label>
      {Object.keys(publishedPapers).map((key) => (
        <div key={key} className="mb-2 flex items-center space-x-2">
          <input
            type="text"
            placeholder="Teacher ID"
            value={publishedPapers[key].teacherId}
            onChange={(e) => handlePaperChange(key, "teacherId", e.target.value)}
            required
            maxLength={5}
            className="w-1/4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <input
            type="number"
            placeholder="Ranking"
            value={publishedPapers[key].ranking}
            onChange={(e) => handlePaperChange(key, "ranking", parseInt(e.target.value))}
            className="w-1/4 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={publishedPapers[key].isCorrespondingAuthor}
              onChange={(e) => handlePaperChange(key, "isCorrespondingAuthor", e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
            />
            <span>Corresponding Author</span>
          </label>
          <button
            type="button"
            onClick={() => handleDeletePaper(key)}
            className="px-3 py-2 bg-red-500 text-white rounded-md"
          >
            Delete
          </button>
        </div>
      ))}
      <button type="button" onClick={handleAddPaper} className="px-3 py-2 bg-blue-500 text-white rounded-md mt-2">
        Add Author
      </button>
    </div>
  );
};

export default PublishedPapersInput;
