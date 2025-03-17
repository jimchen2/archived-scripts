import type { NextApiRequest, NextApiResponse } from "next";
import dbConnect from "../../db/dbConnect";
import Document from "../../models/document.model";

function getRelevantSnippet(body: string, searchTerm: string, isTitleMatch: boolean): string {
  const charLimit = 300;
  if (isTitleMatch) {
    return body.substring(0, charLimit);
  } else {
    const index = body.toLowerCase().indexOf(searchTerm.toLowerCase());
    const start = Math.max(index - Math.floor(charLimit / 2), 0);
    const end = Math.min(start + charLimit, body.length);
    return body.substring(start, end);
  }
}

function formatDateToYYYYMMDD(date: Date): string {
  return date.toISOString().slice(0, 10).replace(/-/g, '');
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  await dbConnect();

  if (req.method === "GET") {
    const { query } = req.query;

    try {
      let documents = [];

      if (query && typeof query === "string") {
        const regex = new RegExp(query, "i");

        // Create a base query object
        const baseQuery: any = {
          access: 1,
          $or: [{ title: regex }, { body: regex }, { type: regex }],
        };

        // Check if the query is a valid date in YYYYMMDD format
        if (/^\d{8}$/.test(query)) {
          const year = parseInt(query.slice(0, 4));
          const month = parseInt(query.slice(4, 6)) - 1; // Months are 0-indexed in JavaScript
          const day = parseInt(query.slice(6, 8));
          const startDate = new Date(Date.UTC(year, month, day));
          const endDate = new Date(Date.UTC(year, month, day + 1));

          baseQuery.$or.push({
            date: {
              $gte: startDate,
              $lt: endDate
            }
          });
        }

        // Use lean() for faster query execution
        documents = await Document.find(baseQuery)
          .select('title date type body')
          .sort({ date: -1 })
          .lean()
          .exec();

        documents = documents.map((doc) => {
          const isTitleMatch = regex.test(doc.title);
          const snippet = getRelevantSnippet(doc.body, query, isTitleMatch);

          return {
            title: doc.title,
            date: doc.date.toISOString(), // Convert date to ISO string
            dateString: formatDateToYYYYMMDD(doc.date), // Add YYYYMMDD format
            type: doc.type,
            body: snippet,
            isTitleMatch,
            isBodyMatch: !isTitleMatch && regex.test(doc.body),
          };
        });
      }
      res.status(200).json(documents);
    } catch (err) {
      res.status(500).json({ message: "Error searching for documents", error: err });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}