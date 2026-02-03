import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";

export default function Home() {
  const router = useRouter();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const currentPath = router.query.path ? router.query.path.join("/") : "";

  useEffect(() => {
    if (router.isReady) {
      fetchItems(currentPath);
    }
  }, [router.isReady, currentPath]);

  const fetchItems = async (prefix) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/list-objects?prefix=${encodeURIComponent(prefix)}`
      );
      console.log(response);
      if (!response.ok) {
        throw new Error("Failed to fetch items");
      }
      const data = await response.json();
      setItems(data.filter((item) => item.path !== prefix));
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const getParentPath = (path) => {
    const parts = path.split("/");
    return parts.slice(0, -1).join("/");
  };

  if (loading)
    return (
      <div className="flex justify-center items-center h-screen">
        Loading...
      </div>
    );
  if (error)
    return (
      <div className="flex justify-center items-center h-screen text-red-500">
        Error: {error}
      </div>
    );

  const allItems = [
    { name: ".", path: currentPath, type: "directory" },
    ...(currentPath
      ? [{ name: "..", path: getParentPath(currentPath), type: "directory" }]
      : []),
    ...items.filter(
      (item) => !(item.type === "directory" && item.path === currentPath)
    ),
  ];
  return (
    <div className="container mx-auto p-4 max-w-[600px]">
      <h1 className="text-3xl font-bold mb-4">My S3 Bucket</h1>
      <div className="bg-gray-100 p-2 rounded mb-4">
        Current Path: {`/` + currentPath}
      </div>
      <ul className="space-y-2">
        {allItems.map((item) => (
          <li
            key={item.path}
            className="border p-2 rounded hover:bg-gray-50 flex justify-between items-center"
          >
            <div>
              {item.type === "directory" ? (
                <Link href={`/${item.path}`}>
                  <span className="text-blue-500 hover:underline cursor-pointer">
                    📁 {item.name}
                  </span>
                </Link>
              ) : (
                <span>
                  📄 {item.name} - {item.size} bytes - Last modified:{" "}
                  {new Date(item.lastModified).toLocaleString()}
                </span>
              )}
            </div>
            {item.type !== "directory" &&
              item.name !== "." &&
              item.name !== ".." && (
                <a
                  href={`https://public.jimchen.me/${item.path}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-1 px-2 rounded"
                >
                  Open
                </a>
              )}
          </li>
        ))}
      </ul>
    </div>
  );
}
