// SignIn.js
import React, { useState, useEffect } from "react";
import { Container, Form, Button, Row, Col } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import Cookies from "js-cookie";
import { fetchUser } from "../FetchUser";
import { BACKEND_URL } from "../config";

const LOGIN_API_URL = `${BACKEND_URL}/auth/login`;

function CustomModal({ show, onClose, title, content }) {
  useEffect(() => {
    const handleEscapeKey = (event) => {
      if (event.keyCode === 27) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscapeKey);

    return () => {
      document.removeEventListener("keydown", handleEscapeKey);
    };
  }, [onClose]);

  if (!show) {
    return null;
  }

  return (
    <div className="modal" style={{ display: "block" }}>
      <div className="modal-dialog">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">{title}</h5>
            <button type="button" className="close" onClick={onClose}>
              <span>&times;</span>
            </button>
          </div>
          <div className="modal-body">{content}</div>
          <div className="modal-footer">
            <Button variant="secondary" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function SignIn() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [modalContent, setModalContent] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const validateAndNavigate = async () => {
      try {
        const userDetails = await fetchUser();
        if (userDetails) {
          // User is already logged in, navigate to homepage or dashboard
          navigate("/");
        }
      } catch (error) {
        console.error("Error validating user:", error);
      }
    };

    validateAndNavigate();
  }, [navigate]);

  const handleCloseModal = () => {
    setShowModal(false);
    setModalContent("");
  };

  const handleShowModal = (message) => {
    setModalContent(message);
    setShowModal(true);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const response = await fetch(LOGIN_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        Cookies.set("token", data.token, { expires: 7 });
        navigate("/");
      } else {
        const errorData = await response.text();
        const errorMessage = errorData.slice(0, 100); // Get the first 100 characters of the error message
        handleShowModal(errorMessage || "An error occurred during Login.");
      }
    } catch (networkError) {
      handleShowModal("Network error. Please try again later.");
    }
  };

  return (
    <Container className="my-4">
      <Row className="justify-content-md-center">
        <Col md={6}>
          <h2>Login</h2>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3" controlId="formBasicUsername">
              <Form.Label>Username</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formBasicPassword">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </Form.Group>

            <Button variant="primary" type="submit">
              Sign In
            </Button>
          </Form>
          <div className="mt-3">
            Don't have an account? <Link to="/register">Register Here</Link>
          </div>
        </Col>
      </Row>

      <CustomModal
        show={showModal}
        onClose={handleCloseModal}
        title="Sign In Status"
        content={modalContent}
      />
    </Container>
  );
}

export default SignIn;