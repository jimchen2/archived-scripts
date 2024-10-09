import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "DELETE") {
    const { id } = req.body;

    try {
      // Delete related PublishedPaper records first
      await prisma.publishedPaper.deleteMany({
        where: { paperId: id },
      });

      // Then delete the Paper record
      await prisma.paper.delete({
        where: { id },
      });

      res.status(200).json({ message: "Paper deleted successfully" });
    } catch (error) {
      res
        .status(500)
        .json({ error: "An error occurred while deleting the paper." });
    }
  } else {
    res.setHeader("Allow", ["DELETE"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
