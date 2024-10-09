// pages/_app.js
import { useState } from 'react';
import '../styles/globals.css';
import Navbar from '../components/navbar/Navbar';
import Sidebar from '../components/sidebar/Sidebar';

function MyApp({ Component, pageProps }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar toggleSidebar={toggleSidebar} />
      <div className="flex flex-1">
        <Sidebar isOpen={isSidebarOpen}/>
        <main className={`flex-1 transition-all duration-300`}>
          <div className="p-4">
          <br/>
          <br/>
          <br/>
          <br/>
          <Component {...pageProps} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default MyApp;