import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Form, FormControl, Button } from "react-bootstrap";

const SearchBar = () => {
  const [query, setQuery] = useState("");
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  
  const navigate = useNavigate();

  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    }
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim() === "") {
      return;
    }
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  const linkStyle = {
    display: "flex",
    alignItems: "center",
    marginRight: "auto",
    textDecoration: "none", 
  };

  return (
    <>
      <Form
        inline
        onSubmit={handleSearch}
        style={{
          position: 'sticky',
          top: 0, 
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          zIndex: 999,
          background: '#f2f2f2',
        }}
      >
        <Link to="/" style={linkStyle}>
          <img
            style={{ maxHeight: "40px", margin: "10px" }}
            src="/favicon.ico"
            alt="home"
          />
          <span
            style={{ fontSize: "25px", color: "black", fontWeight: "bold" }}
          >
            豆瓣小组名
          </span>
        </Link>
        <FormControl
          type="text"
          placeholder="搜索内容"
          style={{ maxWidth: windowWidth < 500 ? "200px" : "300px", marginRight: "10px" }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="outline-success" type="submit" className="ml-2">
          搜索
        </Button>
      </Form>
    </>
  );
};

export default SearchBar;
