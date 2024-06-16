"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";

const SearchBar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search/${searchQuery}`);
    }
  };

  return (
    <div className="flex items-center ml-auto mr-4 md:mr-8">
      <form onSubmit={handleSearch} className="flex items-center">
        <input
          type="text"
          className="px-4 py-2 rounded-full bg-gray-200 focus:outline-none"
          placeholder="搜索我的博客..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit" className="px-4 py-2 bg-white text-gray-800 rounded-full border border-gray-300">
          搜索
        </button>
      </form>
    </div>
  );
};

export default SearchBar;
