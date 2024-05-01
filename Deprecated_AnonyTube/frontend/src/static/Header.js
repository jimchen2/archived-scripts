import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Cookies from "js-cookie";
import { Container, Navbar, Nav, Button } from "react-bootstrap";
import { fetchUser } from "../FetchUser";

const Header = () => {
  const [username, setUsername] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const getUserDetails = async () => {
      const userDetails = await fetchUser();
      if (userDetails) {
        setUsername(userDetails.username);
      } else {
        console.log("No user details found or user is not logged in.");
      }
    };

    getUserDetails();
  }, []);

  const handleLogout = () => {
    Cookies.remove("token");
    setUsername(null);
    navigate("/login");
  };

  // Inline style for max-width of the header content
  const headerContentStyle = {
    maxWidth: "700px",
    width: "100%",
    margin: "0 auto",
  };

  return (
    <Navbar style={{ ...headerContentStyle, backgroundColor: "lightgray" }} expand="lg">

      <Container>
        <Navbar.Brand as={Link} to="/" className="mr-auto">
          AnonyTube
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav" className="justify-content-end">
          <Nav className="align-items-center">
            <Nav.Link as={Link} to="/upload" className="mx-2">
              Upload
            </Nav.Link>
            {username ? (
              <>
                <Nav.Link className="mx-2">
                  {username}
                </Nav.Link>
                <Button
                  variant="outline-secondary"
                  onClick={handleLogout}
                  className="mx-2"
                >
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Nav.Link as={Link} to="/register" className="mx-2">
                  Register
                </Nav.Link>
                <Nav.Link as={Link} to="/signin" className="mx-2">
                  Login
                </Nav.Link>
              </>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Header;
