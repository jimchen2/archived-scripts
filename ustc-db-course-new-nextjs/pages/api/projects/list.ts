// Get Project(s) API
import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "GET") {
    const { id } = req.query;

    try {
      let projects;

      if (id) {
        // Fetch specific project by ID
        projects = await prisma.project.findMany({
          where: { id: id as string },
          include: {
            projectParticipants: {
              include: {
                teacher: true,
              },
            },
          },
        });
      } else {
        // Fetch all projects
        projects = await prisma.project.findMany({
          include: {
            projectParticipants: {
              include: {
                teacher: true,
              },
            },
          },
        });
      }

      res.status(200).json(projects);
    } catch (error) {
      res.status(500).json({ error: "An error occurred while fetching the projects." });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
