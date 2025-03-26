import { Card, Button } from 'react-bootstrap';

function BlogDetail({ selectedBlog }) {
  if (!selectedBlog) {
    return (
      <div className="h-100 d-flex align-items-center justify-content-center">
        <p className="text-muted">Select a blog from the left to view details</p>
      </div>
    );
  }

  return (
    <div className="h-100 overflow-auto p-4">
      <Card border="light">
        <Card.Body>
          <Card.Title as="h1">{selectedBlog.title}</Card.Title>
          <Card.Subtitle className="mb-3 text-muted">
            Published: {new Date(selectedBlog.pub_date).toLocaleString()}
          </Card.Subtitle>
          <Card.Text>{selectedBlog.description}</Card.Text>
          <Button
            variant="primary"
            href={selectedBlog.link}
            target="_blank"
            rel="noopener noreferrer"
          >
            Read full article
          </Button>
        </Card.Body>
      </Card>
    </div>
  );
}

export default BlogDetail;
