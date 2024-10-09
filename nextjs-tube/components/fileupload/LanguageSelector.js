import React from 'react';

const LanguageSelector = ({ language, setLanguage }) => {
  return (
    <div className="mb-4  max-w-[150px]">
      <label className="block text-md">Language</label>
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="block w-full mt-1 p-1 rounded-lg hover:bg-gray-200 bg-white ring-1"
      >
        <option value="en-US">English</option>
        <option value="ru-RU">Russian</option>
        <option value="zh-CN">Chinese</option>
      </select>
    </div>
  );
};

export default LanguageSelector;
