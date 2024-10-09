import React from "react";
import Image from "next/image";
import "tailwindcss/tailwind.css";

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white py-5 shadow">
        <h1 className="text-4xl font-bold text-center text-gray-700">
          Welcome to Our Beautiful Home Page
          <br></br>
          <br></br>
          <br></br>
        </h1>{" "}
      </header>
      <main className="container mx-auto py-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="relative w-full h-64">
            <Image
              src="https://source.unsplash.com/300x300/?nature,water"
              alt="Scenic Image 1"
              fill
              style={{ objectFit: "cover" }}
              className="rounded-lg shadow-md"
            />
          </div>
          <div className="relative w-full h-64">
            <Image
              src="https://source.unsplash.com/300x300/?nature,mountain"
              alt="Scenic Image 2"
              fill
              style={{ objectFit: "cover" }}
              className="rounded-lg shadow-md"
            />
          </div>
          <div className="relative w-full h-64">
            <Image
              src="https://source.unsplash.com/300x300/?nature,forest"
              alt="Scenic Image 3"
              fill
              style={{ objectFit: "cover" }}
              className="rounded-lg shadow-md"
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default HomePage;
