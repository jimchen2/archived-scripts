import React, { useEffect, useRef } from "react";
import { useParams, useLocation } from "react-router-dom";
import { Container } from "react-bootstrap";
import CommentCard from "./CommentCard";
import CommentPager from "./CommentPager";
import { useComments } from "./CommentsApi";

const CommentSection = () => {
  const { id } = useParams();
  const location = useLocation();
  let queryParams = new URLSearchParams(location.search);
  let start = queryParams.get("start");

  const { comments, totalPages } = useComments({ id, start });
  const scrollTargetRef = useRef(null); // Ref to store the current element to scroll to

  useEffect(() => {
    const hash = location.hash;
    if (hash) {
      const targetId = hash.slice(1);
      const elem = document.getElementById(targetId);
      if (elem) {
        scrollTargetRef.current = elem; // Update ref to the new element

        // Smooth scroll to the element with a slight offset
        const y = elem.getBoundingClientRect().top + window.pageYOffset ; // 100px offset
        window.scrollTo({ top: y, behavior: "smooth" });

        // No longer need an observer since we are directly scrolling to the adjusted position
      }
    }
  }, [location, comments]); // Re-run effect if location or comments change

  return (
    <>
      <br />
      <CommentPager pages={totalPages} id={id} current={start || 0} />
      <br />
      <br />
      <Container>
        {comments.map((comment, index) => (
          <CommentCard key={index} index={index} comment={comment} />
        ))}
      </Container>
      <br />
      <CommentPager pages={totalPages} id={id} current={start || 0} />
      <br />
      <br />
    </>
  );
};

export default CommentSection;
