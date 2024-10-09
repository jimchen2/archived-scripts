import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

interface ProjectParticipant {
  teacherId: string;
  ranking: number;
  funding?: number;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "PUT") {
    const { id, name, source, projectType, totalFunding, startYear, endYear, projectParticipants }: { id: string, name: string, source?: string, projectType: number, totalFunding?: number, startYear?: number, endYear?: number, projectParticipants: { [key: string]: ProjectParticipant } } = req.body;

    try {
      // Validate fields
      if (!id || !name || projectType === undefined || !projectParticipants || totalFunding === undefined) {
        return res.status(400).json({ error: "Invalid input data." });
      }

      // Convert projectParticipants object to array
      const projectParticipantsArray = Object.values(projectParticipants);

      // Check if all teachers exist
      const teacherIds = projectParticipantsArray.map(pp => pp.teacherId);
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

      // Check for duplicate rankings within the new project participants
      const rankingSet = new Set();
      for (const pp of projectParticipantsArray) {
        if (rankingSet.has(pp.ranking)) {
          return res.status(400).json({ error: `Duplicate ranking found: ${pp.ranking}` });
        }
        rankingSet.add(pp.ranking);
      }

      // Check if the sum of participant fundings matches total funding
      const totalParticipantFunding = projectParticipantsArray.reduce((sum, pp) => sum + (pp.funding || 0), 0);
      if (totalParticipantFunding !== totalFunding) {
        return res.status(400).json({ error: "Total participant funding does not match total project funding." });
      }

      // Update the Project record
      const project = await prisma.project.update({
        where: { id },
        data: {
          name,
          source,
          projectType,
          totalFunding,
          startYear,
          endYear,
        },
      });

      // Update the related ProjectParticipant records
      await prisma.$transaction(async (tx) => {
        await tx.projectParticipant.deleteMany({
          where: { projectId: id },
        });

        await tx.projectParticipant.createMany({
          data: projectParticipantsArray.map((projectParticipant) => ({
            projectId: id,
            teacherId: projectParticipant.teacherId,
            ranking: projectParticipant.ranking,
            funding: projectParticipant.funding,
          })),
        });
      });

      res.status(200).json(project);
    } catch (error) {
      console.error(error);
      const prismaError = error as { code?: string };
      if (prismaError.code === 'P2002') {
        res.status(409).json({ error: "Teacher's rankings should be unique." });
      } else {
        res.status(500).json({ error: "An error occurred while updating the project." });
      }
    }
  } else {
    res.setHeader("Allow", ["PUT"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
