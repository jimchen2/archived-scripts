// pages/api/papers/create.ts
import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient, Prisma } from "@prisma/client";

const prisma = new PrismaClient();

interface PublishedPaperInput {
  teacherId: string;
  ranking: number;
  isCorrespondingAuthor: boolean;
}

interface PaperInput {
  name: string;
  source: string;
  year: number;
  type: number;
  level: number;
  publishedPapers: { [key: string]: PublishedPaperInput };
}

// Validate input fields
function validateInput(data: PaperInput): { isValid: boolean; error?: string } {
  if (
    !data.name ||
    !data.source ||
    data.year === undefined ||
    data.type === undefined ||
    data.level === undefined ||
    !data.publishedPapers ||
    Object.keys(data.publishedPapers).length === 0
  ) {
    return {
      isValid: false,
      error: "Invalid input data. All fields including source and year are required, and publishedPapers cannot be empty.",
    };
  }
  return { isValid: true };
}

// Validate published papers array
function validatePublishedPapersArray(
  publishedPapersArray: PublishedPaperInput[]
): { isValid: boolean; error?: string } {
  if (publishedPapersArray.length === 0) {
    return {
      isValid: false,
      error: "Published papers array cannot be empty after conversion.",
    };
  }
  return { isValid: true };
}

// Validate teacher existence
async function validateTeachers(
  publishedPapersArray: PublishedPaperInput[]
): Promise<{ isValid: boolean; error?: string }> {
  const teacherIds = publishedPapersArray.map((pp) => pp.teacherId);
  if (teacherIds.length === 0) {
    return { isValid: true };
  }

  const existingTeachers = await prisma.teacher.findMany({
    where: { id: { in: teacherIds } },
    select: { id: true },
  });
  const existingTeacherIds = new Set(existingTeachers.map((t) => t.id));

  for (const teacherId of teacherIds) {
    if (!existingTeacherIds.has(teacherId)) {
      return {
        isValid: false,
        error: `Teacher with ID ${teacherId} does not exist.`,
      };
    }
  }
  return { isValid: true };
}

// Validate corresponding author
function validateCorrespondingAuthor(
  publishedPapersArray: PublishedPaperInput[]
): { isValid: boolean; error?: string } {
  const correspondingAuthors = publishedPapersArray.filter(
    (pp) => pp.isCorrespondingAuthor
  );
  if (correspondingAuthors.length !== 1) {
    return {
      isValid: false,
      error: "There must be exactly one corresponding author.",
    };
  }
  return { isValid: true };
}

// Check for duplicate rankings
function checkDuplicateRankings(
  publishedPapersArray: PublishedPaperInput[]
): { isValid: boolean; error?: string } {
  const rankingSet = new Set();
  for (const pp of publishedPapersArray) {
    if (rankingSet.has(pp.ranking)) {
      return {
        isValid: false,
        error: `Duplicate ranking found: ${pp.ranking}`,
      };
    }
    rankingSet.add(pp.ranking);
  }
  return { isValid: true };
}

// Check for existing paper
async function checkExistingPaper(
  name: string,
  source: string,
  year: number
): Promise<{ isValid: boolean; error?: string }> {
  const existingPaper = await prisma.paper.findFirst({
    where: { name, source, year },
  });

  if (existingPaper) {
    return {
      isValid: false,
      error: "Paper with the same name, source, and year already exists.",
    };
  }
  return { isValid: true };
}

// Create paper and published papers
async function createPaperAndPublishedPapers(
  data: PaperInput,
  publishedPapersArray: PublishedPaperInput[]
) {
  return prisma.$transaction(
    async (tx) => {
      const newPaper = await tx.paper.create({
        data: {
          name: data.name,
          source: data.source,
          year: data.year,
          type: data.type,
          level: data.level,
        },
      });

      if (publishedPapersArray.length > 0) {
        await tx.publishedPaper.createMany({
          data: publishedPapersArray.map((publishedPaper) => ({
            paperId: newPaper.id,
            teacherId: publishedPaper.teacherId,
            ranking: publishedPaper.ranking,
            isCorrespondingAuthor: publishedPaper.isCorrespondingAuthor,
          })),
        });
      }

      return newPaper;
    },
    {
      maxWait: 5000,
      timeout: 10000,
      isolationLevel: Prisma.TransactionIsolationLevel.Serializable,
    }
  );
}

// Handle errors
function handleError(error: unknown, res: NextApiResponse): void {
  console.error("Transaction or other error:", error);

  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    if (error.code === "P2002") {
      return res.status(409).json({
        error: "A record with a unique constraint (e.g., name, source, and year combination) already exists.",
        details: error.meta?.target,
      });
    }
    if (error.code === "P2024" || error.code === "P2008") {
      return res.status(503).json({
        error: "The service is temporarily unavailable due to high load or a long-running operation. Please try again later.",
      });
    }
  }

  res.status(500).json({ error: "An error occurred while creating the paper." });
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    res.setHeader("Allow", ["POST"]);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  const data: PaperInput = req.body;
  const publishedPapersArray: PublishedPaperInput[] = Object.values(data.publishedPapers);

  try {
    // Input validation
    const inputValidation = validateInput(data);
    if (!inputValidation.isValid) {
      return res.status(400).json({ error: inputValidation.error });
    }

    // Published papers array validation
    const arrayValidation = validatePublishedPapersArray(publishedPapersArray);
    if (!arrayValidation.isValid) {
      return res.status(400).json({ error: arrayValidation.error });
    }

    // Teacher validation
    const teacherValidation = await validateTeachers(publishedPapersArray);
    if (!teacherValidation.isValid) {
      return res.status(400).json({ error: teacherValidation.error });
    }

    // Corresponding author validation
    const authorValidation = validateCorrespondingAuthor(publishedPapersArray);
    if (!authorValidation.isValid) {
      return res.status(400).json({ error: authorValidation.error });
    }

    // Ranking validation
    const rankingValidation = checkDuplicateRankings(publishedPapersArray);
    if (!rankingValidation.isValid) {
      return res.status(400).json({ error: rankingValidation.error });
    }

    // Existing paper check
    const paperValidation = await checkExistingPaper(
      data.name,
      data.source,
      data.year
    );
    if (!paperValidation.isValid) {
      return res.status(400).json({ error: paperValidation.error });
    }

    // Create paper
    const paper = await createPaperAndPublishedPapers(data, publishedPapersArray);
    return res.status(201).json(paper);
  } catch (error) {
    handleError(error, res);
  }
}