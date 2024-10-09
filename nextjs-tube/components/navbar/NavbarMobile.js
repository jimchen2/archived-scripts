import { useState } from "react";
import { useRouter } from "next/navigation";

const NavbarMobile = ({ toggleSidebar }) => {
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
      <div className="container mx-auto flex flex-col justify-between items-center py-4 px-4">
        <div className="flex justify-between w-full items-center mb-4">
          <div className="flex items-center">
            <button
              onClick={toggleSidebar}
              className="mr-2 p-2 rounded-full hover:bg-gray-200 focus:outline-none"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <div
              className="text-gray-700 text-lg px-2 py-1 rounded-xl hover:bg-gray-200 cursor-pointer"
              onClick={() => handleNavigation("/")}
            >
              {title}
            </div>
          </div>
          <div
            onClick={() => handleNavigation("/upload")}
            className="px-4 py-1 text-gray-800 rounded-lg hover:bg-gray-200 transition-colors duration-300 cursor-pointer"
          >
            Upload
          </div>
        </div>
        <div className="flex w-full">
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-grow px-4 py-2 rounded-l-lg ring-2 outline-none ring-gray-200 focus:bg-gray-200 focus:shadow-lg"
          />
          <button
            onClick={handleSearchClick}
            className="px-4 py-2 text-gray-800 rounded-r-lg outline-none ring-2 ring-gray-200 hover:bg-gray-200 transition-colors duration-300"
          >
            Search
          </button>
        </div>
      </div>
    </nav>
  );
};

export default NavbarMobile;
