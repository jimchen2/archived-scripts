import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const Search = () => {
  const router = useRouter();
  const { query } = router.query;
  const [results, setResults] = useState([]);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(`/api/search?query=${query || ""}`);
        const data = await response.json();
        setResults(data);
      } catch (error) {
        console.error("Error fetching search results:", error);
      }
    };

    fetchResults();
  }, [query]);

  return (
    <div className="container mx-auto mt-10 flex flex-col items-center grayscale">
      {results.length > 0 ? (
        results.map((video) => (
          <div
            key={video._id}
            className="mb-4 p-4 shadow-md rounded w-full md:w-1/2 hover:bg-gray-200"
          >
            <h2 className="text-lg font-semibold text-center">
              <Link
                href={`/watch?v=${video.s3ObjectKey}`}
                className="hover:underline"
              >
                {video.filename}
              </Link>
            </h2>
            <p className="text-center text-md text-gray-800">
              Language: {video.language} | Tags: {video.tags.join(", ")}
            </p>
          </div>
        ))
      ) : (
        <p>No results found</p>
      )}
    </div>
  );
};

export default Search;
