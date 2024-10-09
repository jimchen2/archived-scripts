import { useState } from "react";
import { useRouter } from "next/navigation";

const NavbarPC = ({ toggleSidebar }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();
  const title = process.env.NEXT_PUBLIC_PLATFORM;

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      router.push(`/?query=${searchQuery}`);
    }
  };

  const handleSearchClick = () => {
    router.push(`/?query=${searchQuery}`);
  };

  const handleNavigation = (path) => {
    router.push(path);
  };

  return (
    <nav className="border shadow-lg">
      <div className="container mx-auto flex flex-row justify-between items-center py-4 px-6">
        <div className="flex items-center">
          <button
            onClick={toggleSidebar}
            className="mr-4 p-2 rounded-full hover:bg-gray-200 focus:outline-none"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div
            className="text-gray-700 text-lg px-4 py-2 rounded-xl hover:bg-gray-200 cursor-pointer"
            onClick={() => handleNavigation("/")}
          >
            {title}
          </div>
        </div>
        <div className="flex flex-row items-center justify-center space-x-8 mr-8">
          <div className="flex">
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="px-4 py-2 rounded-lg ring-2 outline-none ring-gray-200 focus:bg-gray-200 focus:shadow-lg"
            />
            <button
              onClick={handleSearchClick}
              className="px-4 py-2 text-gray-800 rounded-lg outline-none ring-gray-200 hover:bg-gray-200 transition-colors duration-300"
            >
              Search
            </button>
          </div>
          <div
            onClick={() => handleNavigation("/upload")}
            className="px-6 py-2 text-gray-800 rounded-lg hover:bg-gray-200 transition-colors duration-300 cursor-pointer"
          >
            Upload
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavbarPC;