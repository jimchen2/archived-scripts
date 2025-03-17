import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

const NavLinks: React.FC = () => (
  <div className="flex items-center space-x-4">
    <motion.div whileHover={{ scale: 1.05 }}>
      <Link href="/search/%20" className="text-lg p-2 hover:bg-gray-200 transition-colors duration-300">
        Jim Chen's Blog
      </Link>
    </motion.div>
    <motion.div whileHover={{ scale: 1.05 }}>
      <Link href="https://link.jimchen.me" className="text-lg p-2 hover:bg-gray-200 transition-colors duration-300">
        My LinkTree
      </Link>
    </motion.div>
  </div>
);

interface SearchFormProps {
  searchQuery: string;
  setSearchQuery: React.Dispatch<React.SetStateAction<string>>;
  handleSearch: (e: React.FormEvent) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({ searchQuery, setSearchQuery, handleSearch }) => (
  <form onSubmit={handleSearch} className="flex items-center">
    <input
      type="text"
      className="h-10 rounded-l-full px-4 py-2 ring-2 ring-gray-200 hover:bg-gray-200 focus:outline-none"
      placeholder="Search..."
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
    />
    <button type="submit" className="h-10 rounded-r-full bg-white px-4 py-2 text-gray-800 ring-2 ring-gray-200 hover:bg-gray-200">
      Search
    </button>
  </form>
);

const NavbarLarge: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search/${searchQuery}`);
    }
  };

  return (
    <header className="fixed top-0 z-50 w-full bg-white shadow-md font-quicksand font-bold">
      <nav className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <NavLinks />
          <div className="flex items-center">
            <SearchForm searchQuery={searchQuery} setSearchQuery={setSearchQuery} handleSearch={handleSearch} />
          </div>
        </div>
      </nav>
    </header>
  );
};

export default NavbarLarge;
