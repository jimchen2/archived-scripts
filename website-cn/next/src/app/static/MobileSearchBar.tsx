"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

const MobileSearchBar = () => {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) router.push(`/search/${query}`);
  };

  return (
    <form onSubmit={handleSearch} className="flex mt-4 px-4 items-center">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索我的博客..."
        className="w-full bg-gray-200 py-2 px-4 rounded-full focus:outline-none"
      />
      <button className="bg-white text-gray-800 border border-gray-300 px-4 py-2 rounded-full">
        搜索
      </button>
    </form>
  );
};

export default MobileSearchBar;
