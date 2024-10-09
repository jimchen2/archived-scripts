// components/navbar/Navbar.js
import { useEffect, useState } from "react";
import NavbarPC from "./NavbarPC";
import NavbarMobile from "./NavbarMobile";

const Navbar = ({ toggleSidebar }) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 z-10 bg-white">
    {isMobile ? <NavbarMobile toggleSidebar={toggleSidebar} /> : <NavbarPC toggleSidebar={toggleSidebar} />}
    </div>
  );
};

export default Navbar;