import { useState } from "react";
import { useRouter } from "next/navigation";
import SearchForm from "../components/search/SearchForm";
import VideoGrid from "../components/search/VideoGrid";

export default function Search({ initialVideos, initialTotalCount }) {
  const router = useRouter();
  const [videos, setVideos] = useState(initialVideos);
  const [totalCount, setTotalCount] = useState(initialTotalCount);
  const [isLoading, setIsLoading] = useState(false);
  const [searchParams, setSearchParams] = useState({
    query: "",
    language: "",
    tag: "",
    filter: "",
    sort: "random",
    start: 0,
    end: 10,
  });

  const handleSearch = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const queryString = new URLSearchParams(searchParams).toString();
    const res = await fetch(`/api/search?${queryString}`);
    const data = await res.json();

    setVideos(data.videos);
    setTotalCount(data.totalCount);
    setIsLoading(false);

    router.push(`/search?${queryString}`, undefined, { shallow: true });
  };

  const handleInputChange = (e) => {
    setSearchParams({ ...searchParams, [e.target.name]: e.target.value });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <SearchForm
        searchParams={searchParams}
        handleInputChange={handleInputChange}
        handleSearch={handleSearch}
      />
      {isLoading ? (
        <p className="text-center">Loading...</p>
      ) : (
        <>
          <p className="mb-4">Total results: {totalCount}</p>
          <VideoGrid videos={videos} />
        </>
      )}
    </div>
  );
}
