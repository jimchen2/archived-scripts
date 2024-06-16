import type { NextApiRequest, NextApiResponse } from "next";
import dbConnect from "../../db/dbConnect";
import Blog from "../../app/models/blog.model";

interface BlogSnippet {
  title: string;
  date: string;
  type: string;
  body: string;
  isTitleMatch: boolean;
  isBodyMatch: boolean;
}

function escapeRegex(text: string): string {
  return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
}

function getRelevantSnippet(
  body: string,
  searchTerm: string,
  isTitleMatch: boolean
): string {
  if (isTitleMatch) {
    return body.substring(0, 150);
  } else {
    const index = body.toLowerCase().indexOf(searchTerm.toLowerCase());
    const start = Math.max(index - 75, 0);
    const end = Math.min(start + 150, body.length);
    return body.substring(start, end);
  }
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  await dbConnect();

  if (req.method === "GET") {
    const { query } = req.query;

    try {
      let blogs;
      
      if (query && typeof query === "string") {
        const escapedQuery = escapeRegex(query);
        const regex = new RegExp(escapedQuery, "i");

        blogs = await Blog.find();
        blogs = blogs
          .map((blog) => {
            const isTitleMatch = regex.test(blog.title);
            const isBodyMatch = regex.test(blog.body);
            const snippet = getRelevantSnippet(blog.body, query, isTitleMatch);

            return {
              title: blog.title,
              date: blog.date,
              type: blog.type,
              body: snippet,
              isTitleMatch,
              isBodyMatch,
            };
          })
          .filter((blog) => blog.isTitleMatch || blog.isBodyMatch);
      } else {
        blogs = await Blog.find();
      }

      // Sort blogs by date in descending order
      blogs.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

      res.status(200).json(blogs);
    } catch (err) {
      res
        .status(500)
        .json({ message: "Error searching for blog entries", error: err });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
