import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Header from "./static/Header";
import Register from "./register&login/Register";
import SignIn from "./register&login/SignIn";
import VideoList from "./video/Home";
import UserProfile from "./static/UserProfile"; // Import the UserProfile component
import VideoUpload from "./upload/VideoUpload"; // Import the component
import VideoDetail from './video/VideoDetail';

const App = () => {
  return (
    <Router>
      <div>
        <Header />
        <Routes>
          <Route path="/" element={<VideoList />} />
          <Route path="/register" element={<Register />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/user/:userID" element={<UserProfile />} />
          <Route path="/upload" element={<VideoUpload />} />
          <Route path="/video/:id" element={<VideoDetail />} />

        </Routes>
      </div>
    </Router>
  );
};

export default App;
