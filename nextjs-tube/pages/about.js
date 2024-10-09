import { useEffect, useState } from "react";

// pages/about.js
const title = process.env.NEXT_PUBLIC_PLATFORM;

function About() {
  return (
    <div className="min-h-screen p-8">
      <main className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-light mb-6">About {title}</h1>
        <div className="space-y-4 text-gray-900">
          <p>{title} is a chill spot for self-hosting/indexing videos.</p>

          <ul className="list-disc list-inside pl-4">
            <li>Embed videos from YouTube, Bilibili, VK, etc.</li>
            <li>No copyright issues</li>
            <li>No distractions</li>
            <li>
              Multi-language transcription for uploads using{" "}
              <a
                href="https://aws.amazon.com/"
                className="text-gray-900 underline"
              >
                AWS
              </a>
            </li>
          </ul>
          <p>
            Videos can be sourced from legal download sites like{" "}
            <a href="https://archive.org/" className="text-gray-900 underline">
              archive.org
            </a>{" "}
            or from YouTube with a Creative Commons license.
          </p>

          <p>
            Want to contribute or self-host? Check out{" "}
            <a
              href="https://github.com/jimchen2/nextjs-tube"
              className="text-gray-900 underline"
            >
              GitHub
            </a>{" "}
            or{" "}
            <a
              href="https://hub.docker.com/r/jimchen2/nextjs-tube"
              className="text-gray-900 underline"
            >
              Docker
            </a>
            .
          </p>

          <p>
            Report issues to{" "}
            <a
              href="mailto:jimchen4214@gmail.com"
              className="text-gray-900 underline"
            >
              admin
            </a>
            .
          </p>
        </div>
      </main>
    </div>
  );
}

export default About;
