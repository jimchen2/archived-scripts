import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "GET") {
    const { id } = req.query;

    try {
      let papers;

      if (id) {
        // Fetch specific paper by ID
        papers = await prisma.paper.findMany({
          where: { id: parseInt(id as string) },
          include: {
            publishedPapers: {
              include: {
                teacher: true,
              },
            },
          },
        });
      } else {
        // Fetch all papers
        papers = await prisma.paper.findMany({
          include: {
            publishedPapers: {
              include: {
                teacher: true,
              },
            },
          },
        });
      }

      res.status(200).json(papers);
    } catch (error) {
      res
        .status(500)
        .json({ error: "An error occurred while fetching the papers." });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
