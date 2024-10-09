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
  if (req.method === "POST") {
    const {
      name,
      source,
      year,
      type,
      level,
      publishedPapers,
    }: {
      name: string;
      source: string;
      year: number;
      type: number;
      level: number;
      publishedPapers: { [key: string]: PublishedPaper };
    } = req.body;

    try {
      // Validate fields
      if (
        !name ||
        type === undefined ||
        level === undefined ||
        !publishedPapers
      ) {
        return res.status(400).json({ error: "Invalid input data." });
      }

      // Convert publishedPapers object to array
      const publishedPapersArray = Object.values(publishedPapers);

      // Check if all teachers exist
      const teacherIds = publishedPapersArray.map((pp) => pp.teacherId);
      const existingTeachers = await prisma.teacher.findMany({
        where: { id: { in: teacherIds } },
        select: { id: true },
      });
      const existingTeacherIds = new Set(existingTeachers.map((t) => t.id));

      for (const teacherId of teacherIds) {
        if (!existingTeacherIds.has(teacherId)) {
          return res
            .status(400)
            .json({ error: `Teacher with ID ${teacherId} does not exist.` });
        }
      }

      // Check if there is only one corresponding author
      const correspondingAuthors = publishedPapersArray.filter(
        (pp) => pp.isCorrespondingAuthor
      );
      if (correspondingAuthors.length !== 1) {
        return res
          .status(400)
          .json({ error: "There must be exactly one corresponding author." });
      }

      // Check for duplicate rankings
      const rankingSet = new Set();
      for (const pp of publishedPapersArray) {
        if (rankingSet.has(pp.ranking)) {
          return res
            .status(400)
            .json({ error: `Duplicate ranking found: ${pp.ranking}` });
        }
        rankingSet.add(pp.ranking);
      }

      // Check if a paper with the same name, source, and year already exists
      const existingPaper = await prisma.paper.findFirst({
        where: { name, source, year },
      });

      if (existingPaper) {
        return res
          .status(400)
          .json({
            error: "Paper with the same name, source, and year already exists.",
          });
      }

      // Create the paper and associated published papers
      const paper = await prisma.$transaction(async (tx) => {
        const newPaper = await tx.paper.create({
          data: {
            name,
            source,
            year,
            type,
            level,
          },
        });

        await tx.publishedPaper.createMany({
          data: publishedPapersArray.map((publishedPaper) => ({
            paperId: newPaper.id,
            teacherId: publishedPaper.teacherId,
            ranking: publishedPaper.ranking,
            isCorrespondingAuthor: publishedPaper.isCorrespondingAuthor,
          })),
        });

        return newPaper;
      });

      res.status(201).json(paper);
    } catch (error) {
      console.error(error);
      const prismaError = error as { code?: string };
      if (prismaError.code === "P2002") {
        res
          .status(409)
          .json({
            error: "A record with the same primary key already exists.",
          });
      } else {
        res
          .status(500)
          .json({ error: "An error occurred while creating the paper." });
      }
    }
  } else {
    res.setHeader("Allow", ["POST"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
