import { useState, useEffect } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import BlogList from '../components/BlogList';
import BlogDetail from '../components/BlogDetail';

export default function Home() {
  const [blogs, setBlogs] = useState([]);
  const [selectedBlog, setSelectedBlog] = useState(null);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const limit = 10;

  // Fetch initial blogs metadata
  const fetchBlogs = async (newOffset) => {
    if (loading || !hasMore) return;
    setLoading(true);
    
    try {
      const response = await fetch(`/api/getblogsmetadata?offset=${newOffset}&limit=${limit}`);
      const data = await response.json();
      
      if (data.length < limit) setHasMore(false);
      setBlogs(prev => [...prev, ...data]);
      setOffset(newOffset + limit);
    } catch (error) {
      console.error('Error fetching blogs:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch single blog
  const fetchBlog = async (id) => {
    try {
      const response = await fetch(`/api/getblog?id=${id}`);
      const data = await response.json();
      if (data.success) {
        setSelectedBlog(data.blog);
        window.history.pushState({}, '', `/?id=${id}`);
      }
    } catch (error) {
      console.error('Error fetching blog:', error);
    }
  };

  // Initial load and URL check
  useEffect(() => {
    fetchBlogs(0);
    
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    if (id) fetchBlog(id);
  }, []);

  // Infinite scroll handler
  const handleScroll = (e) => {
    const bottom = e.target.scrollHeight - e.target.scrollTop <= e.target.clientHeight + 100;
    if (bottom && !loading && hasMore) {
      fetchBlogs(offset);
    }
  };

  return (
    <Container fluid className="vh-100 d-flex">
      <Row className="flex-grow-1">
        <Col md={5} className="border-end p-0">
          <BlogList
            blogs={blogs}
            selectedBlog={selectedBlog}
            onBlogSelect={fetchBlog}
            onScroll={handleScroll}
            loading={loading}
            hasMore={hasMore}
          />
        </Col>
        <Col md={7} className="p-0">
          <BlogDetail selectedBlog={selectedBlog} />
        </Col>
      </Row>
    </Container>
  );
}
