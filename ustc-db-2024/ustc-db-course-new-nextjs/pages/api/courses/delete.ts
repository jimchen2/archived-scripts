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
      // Delete related TaughtCourse records first
      await prisma.taughtCourse.deleteMany({
        where: { courseId: id },
      });

      // Then delete the Course record
      await prisma.course.delete({
        where: { id },
      });

      res.status(200).json({ message: "Course deleted successfully" });
    } catch (error) {
      console.error(error);
      res
        .status(500)
        .json({ error: "An error occurred while deleting the course." });
    }
  } else {
    res.setHeader("Allow", ["DELETE"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
