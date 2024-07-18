import React, { Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Container } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import SearchBar from "./SearchBar";

const DiscussionsPage = lazy(() => import("./DiscussionsPage"));
const CommentSection = lazy(() => import("./CommentSection"));
const Topic = lazy(() => import("./Topic"));
const SearchPage = lazy(() => import("./SearchPage"));

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Container style={{ maxWidth: "800px" }}>
        <div>
          <SearchBar />
          <Suspense fallback={<div>Loading...</div>}>
            <Routes>
              <Route path="/" element={<DiscussionsPage />} />
              <Route path="/:id/comment" element={<CommentSection />} />
              <Route path="/:id/" element={<Topic />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="*" element={<></>} />
            </Routes>
          </Suspense>
        </div>
      </Container>
    </BrowserRouter>
  </React.StrictMode>
);
