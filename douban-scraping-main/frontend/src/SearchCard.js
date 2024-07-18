import React from "react";
import { Card } from "react-bootstrap";
import { Link } from "react-router-dom";

function highlightTerm(text, term) {
  const pattern = new RegExp(`(${term})`, "gi");

  return text.replace(pattern, "<mark>$1</mark>");
}

const SearchCard = ({ discussion, query }) => {
  if (!discussion.results.length) {
    return null;
  }

  const extraChars = 20;

  return (
    <Card style={{ margin: "1em 0" }}>
      <Card.Header
        as="h5"
        style={{ display: "flex", justifyContent: "space-between" }}
      >
        <Link to={`/${discussion.id}`} style={{ color: "black" }}>
          {discussion.title}
        </Link>
        <Link
          to={`/${discussion.id}/comment?start=0`}
          style={{ color: "black" }}
        >
          查看评论
        </Link>
      </Card.Header>

      <Card.Body>
        {discussion.results.map((result, index) => {
          const numericId = Math.floor(result.numericId / 500) * 500;
          const replyTimeHash = result.data["Reply Time"]
            .slice(0, 20)
            .replace(/\s/g, "_");

          const highlightedContent = highlightTerm(
            result.data["Reply Content"],
            query
          );
          const highlightedIndex = highlightedContent
            .toLowerCase()
            .indexOf(`<mark>${query.toLowerCase()}</mark>`);
          let start =
            highlightedIndex - extraChars >= 0
              ? highlightedIndex - extraChars
              : 0;
          let end =
            highlightedIndex + query.length + extraChars <
            highlightedContent.length
              ? highlightedIndex + query.length + extraChars
              : highlightedContent.length;

          const visibleContent = highlightedContent.slice(start, end);

          return (
            <div key={index}>
              <Link
                to={`/${discussion.id}/comment?start=${numericId}#${replyTimeHash}`}
                dangerouslySetInnerHTML={{
                  __html: `<span style="color:black;">${visibleContent}</span>`,
                }}
                style={{ color: "black" }}
              />
              <br />
              <br />
            </div>
          );
        })}
      </Card.Body>

      <Card.Footer>
        <small className="text-muted">
          Last updated{" "}
          {discussion.results[0].data &&
            discussion.results[0].data["Reply Time"]}
        </small>
      </Card.Footer>
    </Card>
  );
};

export default SearchCard;
