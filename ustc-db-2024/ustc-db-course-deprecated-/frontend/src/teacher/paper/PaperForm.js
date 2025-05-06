import React from "react";
import { Form, Button } from "react-bootstrap";

const PaperForm = ({
  papers,
  selectedPaper,
  setSelectedPaper,
  ranking,
  setRanking,
  isCorrespondingAuthor,
  setIsCorrespondingAuthor,
  handleSubmit,
}) => {
  return (
    <Form onSubmit={handleSubmit}>
      <Form.Group controlId="paper">
        <Form.Label>Select Paper</Form.Label>
        <Form.Control
          as="select"
          value={selectedPaper}
          onChange={(e) => setSelectedPaper(e.target.value)}
          required
        >
          <option value="">Select a paper</option>
          {papers.map((paper) => (
            <option key={paper.id} value={paper.id}>
              {paper.name}
            </option>
          ))}
        </Form.Control>
      </Form.Group>

      <Form.Group controlId="ranking">
        <Form.Label>Ranking</Form.Label>
        <Form.Control
          type="number"
          value={ranking}
          onChange={(e) => setRanking(e.target.value)}
          required
        />
      </Form.Group>

      <Form.Group controlId="isCorrespondingAuthor">
        <Form.Check
          type="checkbox"
          label="Corresponding Author"
          checked={isCorrespondingAuthor}
          onChange={(e) => setIsCorrespondingAuthor(e.target.checked)}
        />
      </Form.Group>

      <Button variant="primary" type="submit">
        Add Paper
      </Button>
    </Form>
  );
};

export default PaperForm;
