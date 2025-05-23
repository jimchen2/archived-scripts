// pages/index.tsx
import React from "react";
import "tailwindcss/tailwind.css";

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white py-5 shadow">
        <h1 className="text-4xl font-bold text-center text-gray-700">
          Welcome to Our Beautiful Home Page
          <br />
          <br />
          <br />
        </h1>{" "}
      </header>
      <main className="container mx-auto py-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="relative w-full h-64">
            <img src="https://loremflickr.com/300/300/nature,water" alt="Scenic Image 1" style={{ objectFit: "cover" }} className="rounded-lg shadow-md" />
          </div>
        </div>
      </main>
    </div>
  );
};

export default HomePage;
