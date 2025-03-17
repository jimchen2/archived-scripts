import { NextApiRequest, NextApiResponse } from "next";
import dbConnect from "../../db/dbConnect"; // Adjust the path as necessary
import Document from "../../models/document.model";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  await dbConnect();

  if (req.method === "GET") {
    const { title, type } = req.query;

    let query: { title?: string; type?: string } = {};

    if (title) {
      query.title = title as string;
    }

    if (type) {
      query.type = type as string;
    }

    try {
      const document = await Document.findOne(query);
      
      if (!document || document.access !== 1) {
        return res.status(404).json({ message: "Document not found or not accessible" });
      }

      const { access, ...sanitizedDocument } = document.toObject();

      res.status(200).json(sanitizedDocument);
    } catch (err) {
      res.status(500).json({ message: "Error fetching document", error: err });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}