"use client";

import React, { useState, useEffect } from "react";
import NavbarLarge from "./NavbarLarge";
import NavbarSmall from "./NavbarSmall";

const Navbar: React.FC = () => {
  const [isLargeScreen, setIsLargeScreen] = useState(true);

  useEffect(() => {
    const checkScreenSize = () => {
      setIsLargeScreen(window.innerWidth >= 768);
    };
    checkScreenSize();
    window.addEventListener("resize", checkScreenSize);
    return () => window.removeEventListener("resize", checkScreenSize);
  }, []);

  return isLargeScreen ? <NavbarLarge /> : <NavbarSmall />;
};

export default Navbar;
