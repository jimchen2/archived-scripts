// pages/api/projects/create.js
import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

interface ProjectParticipant {
  teacherId: string;
  ranking: number;
  funding?: number;
}

interface ProjectInput {
  id: string;
  name: string;
  source?: string;
  projectType: number;
  totalFunding?: number;
  startYear?: number;
  endYear?: number;
  projectParticipants: { [key: string]: ProjectParticipant };
  projectFileUrl?: string;
}

// Validate required fields
function validateInput(data: ProjectInput): { isValid: boolean; error?: string } {
  if (
    !data.id ||
    !data.name ||
    data.projectType === undefined ||
    !data.projectParticipants ||
    data.totalFunding === undefined
  ) {
    return { isValid: false, error: "Invalid input data." };
  }
  return { isValid: true };
}

// Validate teacher existence
async function validateTeachers(
  projectParticipantsArray: ProjectParticipant[]
): Promise<{ isValid: boolean; error?: string }> {
  const teacherIds = projectParticipantsArray.map((pp) => pp.teacherId);
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

// Check for duplicate rankings
function checkDuplicateRankings(
  projectParticipantsArray: ProjectParticipant[]
): { isValid: boolean; error?: string } {
  const rankingSet = new Set();
  for (const pp of projectParticipantsArray) {
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

// Validate funding amounts
function validateFunding(
  projectParticipantsArray: ProjectParticipant[],
  totalFunding: number | undefined
): { isValid: boolean; error?: string } {
  const totalParticipantFunding = projectParticipantsArray.reduce(
    (sum, pp) => sum + (pp.funding || 0),
    0
  );
  if (totalParticipantFunding !== totalFunding) {
    return {
      isValid: false,
      error: "Total participant funding does not match total project funding.",
    };
  }
  return { isValid: true };
}

// Check for existing project
async function checkExistingProject(
  id: string,
  name: string,
  source: string | undefined
): Promise<{ isValid: boolean; error?: string }> {
  const existingProject = await prisma.project.findFirst({
    where: { id, name, source },
  });

  if (existingProject) {
    return {
      isValid: false,
      error: "Project with the same id, name, and source already exists.",
    };
  }
  return { isValid: true };
}

// Create project and participants
async function createProjectAndParticipants(
  data: ProjectInput,
  projectParticipantsArray: ProjectParticipant[]
) {
  return prisma.$transaction(async (tx) => {
    const newProject = await tx.project.create({
      data: {
        id: data.id,
        name: data.name,
        source: data.source,
        projectType: data.projectType,
        totalFunding: data.totalFunding,
        startYear: data.startYear,
        endYear: data.endYear,
        projectFileUrl: data.projectFileUrl,
      },
    });

    if (projectParticipantsArray.length > 0) {
      await tx.projectParticipant.createMany({
        data: projectParticipantsArray.map((projectParticipant) => ({
          projectId: newProject.id,
          teacherId: projectParticipant.teacherId,
          ranking: projectParticipant.ranking,
          funding: projectParticipant.funding,
        })),
      });
    }

    return newProject;
  });
}

// Handle errors
function handleError(
  error: unknown,
  res: NextApiResponse
): void {
  console.error("Error in /api/projects/create:", error);
  const prismaError = error as { code?: string; message?: string };
  
  if (prismaError.code === "P2002") {
    res.status(409).json({
      error: "A record with the same primary key already exists.",
    });
  } else {
    res.status(500).json({
      error: `An error occurred while creating the project: ${prismaError.message || 'Unknown error'}`,
    });
  }
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== "POST") {
    res.setHeader("Allow", ["POST"]);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  const data: ProjectInput = req.body;
  const projectParticipantsArray = Object.values(data.projectParticipants);

  try {
    // Input validation
    const inputValidation = validateInput(data);
    if (!inputValidation.isValid) {
      return res.status(400).json({ error: inputValidation.error });
    }

    // Teacher validation
    const teacherValidation = await validateTeachers(projectParticipantsArray);
    if (!teacherValidation.isValid) {
      return res.status(400).json({ error: teacherValidation.error });
    }

    // Ranking validation
    const rankingValidation = checkDuplicateRankings(projectParticipantsArray);
    if (!rankingValidation.isValid) {
      return res.status(400).json({ error: rankingValidation.error });
    }

    // Funding validation
    const fundingValidation = validateFunding(
      projectParticipantsArray,
      data.totalFunding
    );
    if (!fundingValidation.isValid) {
      return res.status(400).json({ error: fundingValidation.error });
    }

    // Existing project check
    const projectValidation = await checkExistingProject(
      data.id,
      data.name,
      data.source
    );
    if (!projectValidation.isValid) {
      return res.status(400).json({ error: projectValidation.error });
    }

    // Create project
    const project = await createProjectAndParticipants(data, projectParticipantsArray);
    return res.status(201).json(project);

  } catch (error) {
    handleError(error, res);
  }
}