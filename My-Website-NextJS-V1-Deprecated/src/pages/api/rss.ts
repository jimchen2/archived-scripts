import type { NextApiRequest, NextApiResponse } from "next";
import dbConnect from "../../db/dbConnect";
import Blog from "../../models/document.model";
import { Feed } from 'feed';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  await dbConnect();

  if (req.method === "GET") {
    try {
      // Fetch all blogs
      const allBlogs = await Blog.find({}).sort({ date: -1 }); // Sort by date descending

      // Filter blogs with access === 1
      const blogs = allBlogs.filter(blog => blog.access === 1);

      // Create a new feed
      const feed = new Feed({
        title: "JC's Blog",
        id: "https://jimchen.me/",
        link: "https://jimchen.me/",
        favicon: "https://jimchen.me/icon-512x512.png",
        copyright: `All rights reserved ${new Date().getFullYear()}, JC`,
        updated: blogs.length > 0 ? new Date(blogs[0].date) : new Date(),
        generator: "Next.js using Feed for Node.js",
        author: {
          name: "JC",
          email: "jimchen4214@gmail.com",
        },
      });

      blogs.forEach((blog) => {
        feed.addItem({
          title: blog.title,
          content: blog.body,
          author: [
            {
              name: "JC",
              email: "jimchen4214@gmail.com",
            },
          ],
          date: new Date(blog.date),
          link: `https://jimchen.me?title=${blog.title}`,
          category: [{ name: blog.type }],
        });
      });

      // Set the content type and send the RSS feed
      res.setHeader('Content-Type', 'application/rss+xml');
      res.status(200).send(feed.rss2());

    } catch (err) {
      res.status(500).json({ message: "Error generating RSS feed", error: err });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}