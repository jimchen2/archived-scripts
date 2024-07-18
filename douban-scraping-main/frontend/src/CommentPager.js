import React from "react";
import { useNavigate } from "react-router-dom";
import Pagination from "react-bootstrap/Pagination";

const CommentPager = ({ pages, id, current }) => {
  const navigate = useNavigate();
  const currentPage = Math.floor(current / 500) + 1; // Since 'current' is a start index

  const goToPage = (pageNum) => {
    navigate(`/${id}/comment?start=${(pageNum - 1) * 500}`);
  };

  // Generate page numbers to display
  let pageNumbers = [1, currentPage, currentPage - 1, currentPage + 1, pages].filter(
    (number, index, self) => number > 0 && number <= pages && self.indexOf(number) === index
  );

  // Sort the page numbers to ensure they are in order
  pageNumbers.sort((a, b) => a - b);

  const items = [];

  // Iterate through page numbers and add Pagination.Item or Pagination.Ellipsis as needed
  for (let i = 0; i < pageNumbers.length; i++) {
    // Add ellipsis if there's a gap in the sequence
    if (i > 0 && pageNumbers[i] - pageNumbers[i - 1] > 1) {
      items.push(<Pagination.Ellipsis key={`ellipsis-${pageNumbers[i - 1]}`} />);
    }

    // Add the page number
    items.push(
      <Pagination.Item
        key={pageNumbers[i]}
        active={pageNumbers[i] === currentPage}
        onClick={() => goToPage(pageNumbers[i])}
      >
        {pageNumbers[i]}
      </Pagination.Item>
    );
  }

  return (
    <Pagination>
      <Pagination.Prev onClick={() => goToPage(Math.max(1, currentPage - 1))} disabled={currentPage === 1} />
      {items}
      <Pagination.Next onClick={() => goToPage(Math.min(pages, currentPage + 1))} disabled={currentPage === pages} />
    </Pagination>
  );
};

export default CommentPager;
