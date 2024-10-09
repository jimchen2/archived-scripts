// LoginPage.js
import React, { useState } from "react";
import { Navigate } from "react-router-dom";
import { Container, Form, Button } from "react-bootstrap";
import axios from "axios";
import { backendUrl } from "../config";

const LoginPage = () => {
  const [id, setId] = useState("");
  const [password, setPassword] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${backendUrl}/login`, {
        id,
        password,
      });
      const token = response.data.token;
      localStorage.setItem("token", token);
      setLoggedIn(true);
      setIsAdmin(id === "-1");
    } catch (error) {
      console.error("Login failed:", error);
      alert("Invalid credentials. Please try again.");
    }
  };

  if (loggedIn) {
    if (isAdmin) {
      return <Navigate to="/admin/teachers" />;
    } else {
      return <Navigate to="/home" />;
    }
  }

  return (
    <Container style={{ marginTop: "20px" }}>
      <h2>Login</h2>
      <Form onSubmit={handleLogin}>
        <Form.Group controlId="id">
          <Form.Label>ID</Form.Label>
          <Form.Control
            type="text"
            placeholder="Enter ID"
            value={id}
            onChange={(e) => setId(e.target.value)}
          />
        </Form.Group>

        <Form.Group controlId="password">
          <Form.Label>Password</Form.Label>
          <Form.Control
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Form.Group>

        <Button variant="primary" type="submit" style={{ marginTop: "10px" }}>
          Login
        </Button>
      </Form>
      <br />
      <br />
      <br />
      <br />
      <br />
      <br />
      <br />
    </Container>
  );
};

export default LoginPage;
