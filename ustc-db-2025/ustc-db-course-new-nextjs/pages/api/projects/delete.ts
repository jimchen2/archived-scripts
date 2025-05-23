// Delete Project API
import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === "DELETE") {
    const { id } = req.body;

    try {
      // Delete related ProjectParticipant records first
      await prisma.projectParticipant.deleteMany({
        where: { projectId: id },
      });

      // Then delete the Project record
      await prisma.project.delete({
        where: { id },
      });

      res.status(200).json({ message: "Project deleted successfully" });
    } catch (error) {
      res.status(500).json({ error: "An error occurred while deleting the project." });
    }
  } else {
    res.setHeader("Allow", ["DELETE"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
