"use client";

import { useState } from "react";

const PDFViewer = ({ file }) => (
  <div className="h-screen flex justify-center items-center bg-gray-100">
    <object data={file} type="application/pdf" width="100%" height="100%">
      <p>
      <br/>
      <br/>
      <br/>
      <br/>
      <br/>
        Your browser does not support PDFs.
        <a href={file}>Download the PDF</a>.
      </p>
    </object>
  </div>
);

export default function App() {
  const [pdfFile] = useState("https://jimchen.me/cv.pdf");
  return (
    <div>
      <br />
      <br />
      <br />
      <PDFViewer file={pdfFile} />
    </div>
  );
}
