// Register.js
import React, { useState } from "react";
import { Container, Row, Col, Button } from "react-bootstrap";
import { Link } from "react-router-dom";
import Cookies from "js-cookie";
import RegisterBox from "./RegisterBox";
import { useEffect } from "react";
import { BACKEND_URL } from "../config";

const REGISTER_API_URL = `${BACKEND_URL}/auth/signup`;
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

function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [modalContent, setModalContent] = useState("");

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

    if (password !== confirmPassword) {
      handleShowModal("Passwords do not match.");
      return;
    }

    try {
      const regResponse = await fetch(REGISTER_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      if (regResponse.ok) {
        const loginResponse = await fetch(LOGIN_API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ username, password }),
        });

        if (loginResponse.ok) {
          const data = await loginResponse.json();
          Cookies.set("token", data.token, { expires: 7 });
          window.location.href = "/";
        } else {
          const loginErrorData = await loginResponse.text();
          handleShowModal(loginErrorData || "An error occurred during sign in.");
        }
      } else {
        const regErrorData = await regResponse.json();
        console.log(regResponse);
        handleShowModal(
          regErrorData.message || "An error occurred during registration."
        );
      }
    } catch (error) {
      console.error("Error:", error);
      handleShowModal(error.message || "An unexpected error occurred.");
    }
  };

  return (
    <Container className="my-4">
      <Row className="justify-content-md-center">
        <Col md={6}>
          <h2>Register</h2>
          <RegisterBox
            username={username}
            setUsername={setUsername}
            password={password}
            setPassword={setPassword}
            confirmPassword={confirmPassword}
            setConfirmPassword={setConfirmPassword}
            handleSubmit={handleSubmit}
          />
          <div className="mt-3">
            Already have an account? <Link to="/signin">Sign In Here</Link>
          </div>
        </Col>
      </Row>

      <CustomModal
        show={showModal}
        onClose={handleCloseModal}
        title="Registration Status"
        content={modalContent}
      />
    </Container>
  );
}

export default Register;