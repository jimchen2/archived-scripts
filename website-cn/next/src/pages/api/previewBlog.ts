import type { NextApiRequest, NextApiResponse } from "next";
import dbConnect from "../../db/dbConnect";
import Blog from "../../app/models/blog.model";

interface BlogEntry {
  title: string;
  date: Date;
  uuid: string;
}

type BlogsByType = {
  [key: string]: BlogEntry[];
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  await dbConnect();

  if (req.method === "GET") {
    try {
      // Fetch all blogs
      const blogs = await Blog.find({});

      // Group blogs by type
      const blogsByType: BlogsByType = blogs.reduce((acc: BlogsByType, blog) => {
        if (!acc[blog.type]) {
          acc[blog.type] = [];
        }
        acc[blog.type].push({
          title: blog.title,
          date: new Date(blog.date), // Convert date string to Date object
          uuid: blog.date, // Assuming uuid is intended to be blog.date; adjust if necessary
        });
        return acc;
      }, {});

      // Sort types by the number of blogs in each type (descending)
      const sortedTypes = Object.entries(blogsByType)
        .sort((a, b) => b[1].length - a[1].length)
        .map(([type, blogs]) => ({
          type,
          blogs: blogs.sort((a, b) => {
            // Sort blogs within each type by date (ascending)
            return a.date.getTime() - b.date.getTime();
          }),
        }));

      res.status(200).json(sortedTypes);
    } catch (err) {
      res.status(500).json({ message: "Error fetching blog previews", error: err });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
