import { ListGroup, Spinner, Alert } from 'react-bootstrap';

function BlogList({ blogs, selectedBlog, onBlogSelect, onScroll, loading, hasMore }) {
  return (
    <div 
      className="overflow-auto h-100 p-3"
      onScroll={onScroll}
    >
      <h2 className="mb-3">Blog Posts</h2>
      
      <ListGroup>
        {blogs.map(blog => (
          <ListGroup.Item 
            key={blog.id}
            action
            active={selectedBlog?.id === blog.id}
            onClick={() => onBlogSelect(blog.id)}
            className="mb-2"
          >
            <h5 className="mb-1">{blog.title}</h5>
            <small className="text-muted">
              {new Date(blog.pub_date).toLocaleDateString()}
            </small>
          </ListGroup.Item>
        ))}
      </ListGroup>
      
      {loading && (
        <div className="text-center my-3">
          <Spinner animation="border" role="status" size="sm" className="me-2" />
          <span>Loading more...</span>
        </div>
      )}
      
      {!hasMore && blogs.length > 0 && (
        <Alert variant="info" className="mt-3">
          No more blogs to load
        </Alert>
      )}
    </div>
  );
}

export default BlogList;
