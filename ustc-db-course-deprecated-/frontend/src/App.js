// App.js
import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import Footer from "./footer/Footer";
import { AdminNavbar, RegularNavbar } from "./Navbar";
import LoginPage from "./login/login";
import Teachers from "./admin/teacher/Teachers";
import Projects from "./admin/project/Project";
import Course from "./admin/course/CourseManagement";
import Paper from "./admin/paper/PaperManagement";
import About from "./About";
import { Container } from "react-bootstrap";

import CourseList from "./teacher/course/CourseList";
import AddCourse from "./teacher/course/AddCourse";
import EditCourse from "./teacher/course/EditCourse";

import AddPaper from "./teacher/paper/AddPaper";
import PaperList from "./teacher/paper/PaperList";
import EditPaper from "./teacher/paper/EditPaper";

import TeacherExport from "./teacher/export/TeacherExport";

import SearchTeacher from "./search";

function App() {
  return (
    <Router>
      <Routes>

        <Route
          path="/admin/*"
          element={
            <>
              <AdminNavbar />
              <Container style={{ maxWidth: "800px" }}>
                <Routes>
                  <Route path="/teachers" element={<Teachers />} />
                  <Route path="/projects" element={<Projects />} />
                  <Route path="/course" element={<Course />} />
                  <Route path="/paper" element={<Paper />} />
                </Routes>
              </Container>
            </>
          }
        />

        <Route
          path="/*"
          element={
            <>
              <RegularNavbar />
              <Container style={{ maxWidth: "800px" }}>
                <Routes>
                  <Route path="/" element={<LoginPage />} />
                  <Route path="/about" element={<About />} />
                  <Route path="/course/courselist" element={<CourseList />} />
                  <Route path="/course/addcourse" element={<AddCourse />} />
                  <Route
                    path="/course/edit/:courseId"
                    element={<EditCourse />}
                  />
                  <Route path="/paper/addpaper" element={<AddPaper />} />
                  <Route path="/paper/paperlist" element={<PaperList />} />
                  <Route
                    path="/paper/editpaper/:paperId"
                    element={<EditPaper />}
                  />
                  <Route path="/about" element={<About />} />
                  <Route path="/search" element={<SearchTeacher />} />

                  <Route path="/export" element={<TeacherExport />} />
                </Routes>{" "}
              </Container>

              <Footer />
            </>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
