import React, { useEffect, useState } from "react";
import ReactMarkdown from 'react-markdown';

const About = () => {
  const [content, setContent] = useState('');

  useEffect(() => {
    fetch('/About.md')
      .then((response) => response.text())
      .then((text) => setContent(text));
  }, []);

  return (
    <div>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
};

export default About;
