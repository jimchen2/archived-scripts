import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "GET") {
    const { id } = req.query;

    try {
      let courses;

      if (id) {
        // Fetch specific course by ID
        courses = await prisma.course.findMany({
          where: { id: id as string },
          include: {
            taughtCourses: {
              include: {
                teacher: true,
              },
            },
          },
        });
      } else {
        // Fetch all courses
        courses = await prisma.course.findMany({
          include: {
            taughtCourses: {
              include: {
                teacher: true,
              },
            },
          },
        });
      }

      res.status(200).json(courses);
    } catch (error) {
      console.error(error);
      res
        .status(500)
        .json({ error: "An error occurred while fetching the courses." });
    }
  } else {
    res.setHeader("Allow", ["GET"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
