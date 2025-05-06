// Navbar.js
import React from "react";
import { Navbar, Container, Nav, NavDropdown } from "react-bootstrap";

// Admin Navbar
export const AdminNavbar = () => (
  <Navbar
    style={{ backgroundColor: "#f8f9fa", borderBottom: "2px solid #007bff" }}
    variant="light"
    expand="lg"
  >
    <Container>
      <Navbar.Brand href="/admin" style={{ color: "#007bff" }}>
        管理员面板
      </Navbar.Brand>
      <Navbar.Toggle aria-controls="admin-navbar-nav" />
      <Navbar.Collapse id="admin-navbar-nav">
        <Nav className="me-auto">
          <Nav.Link href="/admin/teachers" style={{ color: "#0056b3" }}>
            教师管理
          </Nav.Link>
          <Nav.Link href="/admin/projects" style={{ color: "#0056b3" }}>
            项目管理
          </Nav.Link>
          <Nav.Link href="/admin/course" style={{ color: "#0056b3" }}>
            课程管理
          </Nav.Link>
          <Nav.Link href="/admin/paper" style={{ color: "#0056b3" }}>
            论文管理
          </Nav.Link>
          <Nav.Link href="/search" style={{ color: "#0056b3" }}>
            search
          </Nav.Link>
          <Nav.Link href="/about" style={{ color: "#0056b3" }}>
            关于作业
          </Nav.Link>
          <Nav.Link
            href="https://jimchen.me/about"
            style={{ color: "#0056b3" }}
          >
            关于我
          </Nav.Link>
        </Nav>
      </Navbar.Collapse>
    </Container>
  </Navbar>
);

// Regular Navbar
export const RegularNavbar = () => (
  <Navbar
    style={{ backgroundColor: "#e9ecef", borderBottom: "2px solid #28a745" }}
    variant="light"
    expand="lg"
  >
    <Container>
      <Navbar.Brand href="/" style={{ color: "#28a745" }}>
        教师管理系统
      </Navbar.Brand>
      <Navbar.Toggle aria-controls="basic-navbar-nav" />
      <Navbar.Collapse id="basic-navbar-nav">
        <Nav className="me-auto">
          <Nav.Link href="/" style={{ color: "#155724" }}>
            登录
          </Nav.Link>
          <NavDropdown
            title="课程"
            id="course-dropdown"
            style={{ color: "#155724" }}
          >
            <NavDropdown.Item href="/course/courselist">
              我的课程
            </NavDropdown.Item>
            <NavDropdown.Item href="/course/addcourse">
              添加课程
            </NavDropdown.Item>
          </NavDropdown>
          <NavDropdown
            title="论文"
            id="paper-dropdown"
            style={{ color: "#155724" }}
          >
            <NavDropdown.Item href="/paper/paperlist">
              我的论文
            </NavDropdown.Item>
            <NavDropdown.Item href="/paper/addpaper">添加论文</NavDropdown.Item>
          </NavDropdown>

          <Nav.Link href="/export" style={{ color: "#155724" }}>
            导出
          </Nav.Link>
          <Nav.Link href="/search" style={{ color: "#0056b3" }}>
            search
          </Nav.Link>

          <Nav.Link href="/about" style={{ color: "#155724" }}>
            关于作业
          </Nav.Link>

          <Nav.Link
            href="https://jimchen.me/about"
            style={{ color: "#155724" }}
          >
            关于我
          </Nav.Link>
        </Nav>
      </Navbar.Collapse>
    </Container>
  </Navbar>
);
