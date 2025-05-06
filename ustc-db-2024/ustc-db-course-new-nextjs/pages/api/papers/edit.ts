import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

interface PublishedPaper {
  teacherId: string;
  ranking: number;
  isCorrespondingAuthor: boolean;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "PUT") {
    const {
      id,
      name,
      source,
      year,
      type,
      level,
      publishedPapers,
    }: {
      id: number;
      name: string;
      source: string;
      year: number;
      type: number;
      level: number;
      publishedPapers: { [key: string]: PublishedPaper };
    } = req.body;

    try {
      // Validate fields
      if (!id || !name || type === undefined || level === undefined || !publishedPapers) {
        return res.status(400).json({ error: "Invalid input data." });
      }

      // Convert publishedPapers object to array
      const publishedPapersArray = Object.values(publishedPapers);

      // Check if all teachers exist
      const teacherIds = publishedPapersArray.map(pp => pp.teacherId);
      const existingTeachers = await prisma.teacher.findMany({
        where: { id: { in: teacherIds } },
        select: { id: true }
      });
      const existingTeacherIds = new Set(existingTeachers.map(t => t.id));

      for (const teacherId of teacherIds) {
        if (!existingTeacherIds.has(teacherId)) {
          return res.status(400).json({ error: `Teacher with ID ${teacherId} does not exist.` });
        }
      }

      // Check if there is only one corresponding author
      const correspondingAuthors = publishedPapersArray.filter(pp => pp.isCorrespondingAuthor);
      if (correspondingAuthors.length !== 1) {
        return res.status(400).json({ error: "There must be exactly one corresponding author." });
      }

      // Check for duplicate rankings within the new published papers
      const rankingSet = new Set();
      for (const pp of publishedPapersArray) {
        if (rankingSet.has(pp.ranking)) {
          return res.status(400).json({ error: `Duplicate ranking found: ${pp.ranking}` });
        }
        rankingSet.add(pp.ranking);
      }

      // Update the Paper record
      const paper = await prisma.paper.update({
        where: { id },
        data: {
          name,
          source,
          year,
          type,
          level,
        },
      });

      // Update the related PublishedPaper records
      await prisma.$transaction(async (tx) => {
        await tx.publishedPaper.deleteMany({
          where: { paperId: id },
        });

        await tx.publishedPaper.createMany({
          data: publishedPapersArray.map((publishedPaper) => ({
            paperId: id,
            teacherId: publishedPaper.teacherId,
            ranking: publishedPaper.ranking,
            isCorrespondingAuthor: publishedPaper.isCorrespondingAuthor,
          })),
        });
      });

      res.status(200).json(paper);
    } catch (error) {
      console.error(error);
      const prismaError = error as { code?: string };
      if (prismaError.code === 'P2002') {
        res.status(409).json({ error: "Teacher's rankings should be unique." });
      } else {
        res.status(500).json({ error: "An error occurred while updating the paper." });
      }
    }
  } else {
    res.setHeader("Allow", ["PUT"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
