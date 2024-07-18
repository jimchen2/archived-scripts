import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import SearchCard from './SearchCard.js';
import BACKEND_URL from './config.js';

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

const SearchPage = () => {
  const [topicIDs, setTopicIDs] = useState([]);
  const [results, setResults] = useState([]);
  const [noResults, setNoResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const query = useQuery().get('q');

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/discussions`)
      .then((response) => response.json())
      .then((data) =>
        setTopicIDs(data.map((item) => ({ id: item['Topic ID'], title: item['Title'] })))
      );
  }, []);

  useEffect(() => {
    const fetchResults = async () => {
      setLoading(true);
      let foundResults = false;
      
      const promises = topicIDs.map(topic =>
        fetch(`${BACKEND_URL}/api/search?query=${query}&discussion=comments.${topic.id}`)
          .then(response => response.json())
          .then(data => {
            if (data.length > 0) {
              foundResults = true;
            }
            return { id: topic.id, title: topic.title, results: data };
          })
      );

      const newResults = await Promise.all(promises);
      setResults(newResults);
      setNoResults(!foundResults);
      setLoading(false);
    };

    if (topicIDs.length > 0) {
      setNoResults(false);
      fetchResults();
    }
  }, [topicIDs, query]);

  return (
    <div>
      {loading ? (
        <p className="loading">加载中...</p>
      ) : (
        <>
          <h3>"{query}"的搜索结果</h3>
          {results.map((result, i) => (
            <SearchCard key={i} discussion={result} query={query} />
          ))}
          {noResults && (
            <h4>
              <br />
              找不到结果
            </h4>
          )}
        </>
      )}
    </div>
  );
};

export default SearchPage;
