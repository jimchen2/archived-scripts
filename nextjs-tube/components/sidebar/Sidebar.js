// components/sidebar/Sidebar.js
import React from "react";
import Link from "next/link";

const Sidebar = ({ isOpen }) => (
  <div
    className={`fixed left-0 w-36 h-full bg-gray-100 shadow-lg transition-all duration-300 ${
      isOpen ? "translate-x-0" : "-translate-x-full"
    }`}
  >
    <nav className="p-4">
      <ul className="space-y-2">
        <br />
        <br />
        <br />
        <br />
        <br />
        <SidebarLink href="/about" icon="📄">
          About
        </SidebarLink>
        <SidebarLink href="/settings" icon="⚙️">
          Settings
        </SidebarLink>
      </ul>
    </nav>
  </div>
);

const SidebarLink = ({ href, icon, children }) => (
  <li>
    <Link href={href}>
      <div className="flex items-center p-2 rounded hover:bg-gray-200">
        <span className="mr-2">{icon}</span>
        <span>{children}</span>
      </div>
    </Link>
  </li>
);

export default Sidebar;
