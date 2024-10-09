import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

interface TaughtCourse {
  teacherId: string;
  year: number;
  term: number;
  teachingHours: number;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === "PUT") {
    const {
      id,
      name,
      totalHours,
      level,
      taughtCourses,
    }: {
      id: string;
      name: string;
      totalHours: number;
      level: number;
      taughtCourses: TaughtCourse[];
    } = req.body;

    try {
      // Validate fields
      if (
        !id ||
        !name ||
        totalHours === undefined ||
        level === undefined ||
        !taughtCourses ||
        !Array.isArray(taughtCourses) || // Check if taughtCourses is an array
        taughtCourses.length === 0
      ) {
        return res.status(400).json({ error: "Invalid input data." });
      }

      // Check if all teachers exist
      const teacherIds = taughtCourses.map((tc) => tc.teacherId);
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

      // Group taughtCourses by year and term and validate teaching hours
      const groupedTeachingHours: { [key: string]: number } = {};

      for (const tc of taughtCourses) {
        if (tc.teachingHours <= 0) {
          return res.status(400).json({ error: "Teaching hours must be greater than 0." });
        }

        const key = `${tc.year}-${tc.term}`;
        if (!groupedTeachingHours[key]) {
          groupedTeachingHours[key] = 0;
        }
        groupedTeachingHours[key] += tc.teachingHours;
      }

      for (const key in groupedTeachingHours) {
        if (groupedTeachingHours[key] !== totalHours) {
          return res.status(400).json({ error: `Total teaching hours for ${key} do not match the specified total hours.` });
        }
      }

      // Update the Course record
      const course = await prisma.course.update({
        where: { id },
        data: {
          name,
          totalHours,
          level,
        },
      });

      // Update the related TaughtCourse records
      await prisma.taughtCourse.deleteMany({
        where: { courseId: id },
      });

      await prisma.taughtCourse.createMany({
        data: taughtCourses.map((taughtCourse) => ({
          courseId: id,
          teacherId: taughtCourse.teacherId,
          year: taughtCourse.year,
          term: taughtCourse.term,
          teachingHours: taughtCourse.teachingHours,
        })),
      });

      res.status(200).json(course);
    } catch (error) {
      console.error(error);
      res
        .status(500)
        .json({ error: "An error occurred while updating the course." });
    }
  } else {
    res.setHeader("Allow", ["PUT"]);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
