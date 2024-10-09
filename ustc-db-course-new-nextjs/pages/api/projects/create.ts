import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

interface ProjectParticipant {
  teacherId: string;
  ranking: number;
  funding?: number;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "POST") {
    const {
      id,
      name,
      source,
      projectType,
      totalFunding,
      startYear,
      endYear,
      projectParticipants,
    }: {
      id: string;
      name: string;
      source?: string;
      projectType: number;
      totalFunding?: number;
      startYear?: number;
      endYear?: number;
      projectParticipants: { [key: string]: ProjectParticipant };
    } = req.body;

    try {
      // Validate fields
      if (
        !id ||
        !name ||
        projectType === undefined ||
        !projectParticipants ||
        totalFunding === undefined
      ) {
        return res.status(400).json({ error: "Invalid input data." });
      }

      // Convert projectParticipants object to array
      const projectParticipantsArray = Object.values(projectParticipants);

      // Check if all teachers exist
      const teacherIds = projectParticipantsArray.map((pp) => pp.teacherId);
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

      // Check for duplicate rankings
      const rankingSet = new Set();
      for (const pp of projectParticipantsArray) {
        if (rankingSet.has(pp.ranking)) {
          return res
            .status(400)
            .json({ error: `Duplicate ranking found: ${pp.ranking}` });
        }
        rankingSet.add(pp.ranking);
      }

      // Check if the sum of participant fundings matches total funding
      const totalParticipantFunding = projectParticipantsArray.reduce(
        (sum, pp) => sum + (pp.funding || 0),
        0
      );
      if (totalParticipantFunding !== totalFunding) {
        return res
          .status(400)
          .json({
            error:
              "Total participant funding does not match total project funding.",
          });
      }

      // Check if a project with the same id, name, and source already exists
      const existingProject = await prisma.project.findFirst({
        where: { id, name, source },
      });

      if (existingProject) {
        return res
          .status(400)
          .json({
            error: "Project with the same id, name, and source already exists.",
          });
      }

      // Create the project and associated project participants
      const project = await prisma.$transaction(async (tx) => {
        const newProject = await tx.project.create({
          data: {
            id,
            name,
            source,
            projectType,
            totalFunding,
            startYear,
            endYear,
          },
        });

        await tx.projectParticipant.createMany({
          data: projectParticipantsArray.map((projectParticipant) => ({
            projectId: newProject.id,
            teacherId: projectParticipant.teacherId,
            ranking: projectParticipant.ranking,
            funding: projectParticipant.funding,
          })),
        });

        return newProject;
      });

      res.status(201).json(project);
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
          .json({ error: "An error occurred while creating the project." });
      }
    }
  } else {
    res.setHeader("Allow", ["POST"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
