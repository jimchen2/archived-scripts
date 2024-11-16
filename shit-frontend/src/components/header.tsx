"use client";

import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();

  return (
    <nav>
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex items-center justify-center h-16 gap-8">
          <button onClick={() => router.push("/")} className="px-3 py-2 rounded hover:bg-gray-100">
            Home
          </button>

          <button onClick={() => router.push("/videos")} className="px-3 py-2 rounded hover:bg-gray-100">
            Videos
          </button>

          <div className="relative group">
            <button className="px-3 py-2 rounded hover:bg-gray-100">Blog</button>
            <div className="absolute hidden group-hover:block w-24 bg-white shadow-lg rounded-md">
              <button onClick={() => router.push("/en")} className="block w-full text-left px-4 py-2 hover:bg-gray-100">
                English
              </button>
              <button onClick={() => router.push("/ru")} className="block w-full text-left px-4 py-2 hover:bg-gray-100">
                Русский
              </button>
              <button onClick={() => router.push("/zh")} className="block w-full text-left px-4 py-2 hover:bg-gray-100">
                中文
              </button>
            </div>
          </div>

          {/* <button onClick={() => router.push("/search")} className="px-3 py-2 rounded hover:bg-gray-100">
            Search
          </button> */}
        </div>
      </div>
    </nav>
  );
}
