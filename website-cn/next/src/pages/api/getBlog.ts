import { NextApiRequest, NextApiResponse } from 'next';
import dbConnect from '../../db/dbConnect'; // Adjust the path as necessary
import Blog from '../../app/models/blog.model';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  await dbConnect();

  if (req.method === 'GET') {
    const { date, type } = req.query;

    let query: { date?: string; type?: string } = {};

    if (date) {
      query.date = date as string;
    }

    if (type) {
      query.type = type as string;
    }

    try {
      const blogs = await Blog.find(query);
      res.status(200).json(blogs);
    } catch (err) {
      res.status(500).json({ message: 'Error fetching blogs', error: err });
    }
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
