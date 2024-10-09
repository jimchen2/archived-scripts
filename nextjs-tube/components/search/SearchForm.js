export default function SearchForm({ searchParams, handleInputChange, handleSearch }) {
    return (
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex flex-wrap -mx-2 mb-4">
          <div className="w-full md:w-1/3 px-2 mb-4">
            <input
              type="text"
              name="query"
              value={searchParams.query}
              onChange={handleInputChange}
              placeholder="Search videos..."
              className="w-full p-2 border rounded"
            />
          </div>
          <div className="w-full md:w-1/3 px-2 mb-4">
            <select
              name="language"
              value={searchParams.language}
              onChange={handleInputChange}
              className="w-full p-2 border rounded"
            >
              <option value="">All Languages</option>
              <option value="en">English</option>
              <option value="es">Spanish</option>
            </select>
          </div>
          <div className="w-full md:w-1/3 px-2 mb-4">
            <input
              type="text"
              name="tag"
              value={searchParams.tag}
              onChange={handleInputChange}
              placeholder="Filter by tag"
              className="w-full p-2 border rounded"
            />
          </div>
        </div>
        <div className="flex flex-wrap -mx-2 mb-4">
          <div className="w-full md:w-1/3 px-2 mb-4">
            <input
              type="text"
              name="filter"
              value={searchParams.filter}
              onChange={handleInputChange}
              placeholder="Exclude tags (comma-separated)"
              className="w-full p-2 border rounded"
            />
          </div>
          <div className="w-full md:w-1/3 px-2 mb-4">
            <select
              name="sort"
              value={searchParams.sort}
              onChange={handleInputChange}
              className="w-full p-2 border rounded"
            >
              <option value="random">Random</option>
              <option value="createdAt">Newest</option>
              <option value="filename">Filename</option>
            </select>
          </div>
          <div className="w-full md:w-1/3 px-2 mb-4">
            <button
              type="submit"
              className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Search
            </button>
          </div>
        </div>
      </form>
    );
  }