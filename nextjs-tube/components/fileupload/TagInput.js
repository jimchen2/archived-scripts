import React, { useState } from "react";

const TagInput = ({ tags, setTags }) => {
  const [tagInput, setTagInput] = useState("");

  const handleTagInputChange = (event) => {
    setTagInput(event.target.value);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addTag();
    }
  };

  const addTag = () => {
    if (tagInput && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput("");
    }
  };

  const removeTag = (tagToRemove) => {
    setTags(tags.filter((tag) => tag !== tagToRemove));
  };

  return (
    <div className="mb-4 max-w-[400px]">
      <label className="block text-md font-medium">Tags</label>
      <div className="flex items-center text-sm">
        <input
          type="text"
          value={tagInput}
          onChange={handleTagInputChange}
          onKeyDown={handleKeyDown}
          placeholder="press enter to add tag"
          className="block w-full mt-1 p-2 ring-1 rounded-lg hover:bg-gray-200 focus:bg-gray-200"
        />
        <button
          onClick={addTag}
          className="ml-3  p-2  mt-1 text-gray-800 rounded-lg text-md hover:bg-gray-200 ring-1 min-w-[100px]"
        >
          Add Tag
        </button>
      </div>
      <div className="mt-2">
        {tags.map((tag, index) => (
          <span
            key={index}
            className="inline-block bg-gray-200 text-gray-800 text-sm px-2 py-1 rounded mr-2"
          >
            {tag}
            <button
              onClick={() => removeTag(tag)}
              className="ml-1 text-gray-500"
            >
              &times;
            </button>
          </span>
        ))}
      </div>
    </div>
  );
};

export default TagInput;
