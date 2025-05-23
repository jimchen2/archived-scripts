import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

interface TaughtCourse {
  teacherId: string;
  year: number;
  term: number;
  teachingHours: number;
}

interface CourseInput {
  id: string;
  name: string;
  totalHours: number;
  level: number;
  taughtCourses: TaughtCourse[];
}

// Validate input data
const validateInput = (input: CourseInput): boolean => {
  return !!(input.id && input.name && input.totalHours !== undefined && input.level !== undefined && input.taughtCourses && Array.isArray(input.taughtCourses) && input.taughtCourses.length > 0);
};

// Check for duplicate course ID
const checkDuplicateCourse = async (id: string) => {
  const existingCourse = await prisma.course.findUnique({
    where: { id },
  });
  return existingCourse;
};

// Validate teachers' existence
const validateTeachers = async (taughtCourses: TaughtCourse[]): Promise<string | null> => {
  const teacherIds = taughtCourses.map((tc) => tc.teacherId);
  const existingTeachers = await prisma.teacher.findMany({
    where: { id: { in: teacherIds } },
    select: { id: true },
  });
  const existingTeacherIds = new Set(existingTeachers.map((t) => t.id));

  for (const teacherId of teacherIds) {
    if (!existingTeacherIds.has(teacherId)) {
      return teacherId;
    }
  }
  return null;
};

// Validate teaching hours
const validateTeachingHours = (taughtCourses: TaughtCourse[], totalHours: number): string | null => {
  const groupedTeachingHours: { [key: string]: number } = {};

  for (const tc of taughtCourses) {
    if (tc.teachingHours <= 0) {
      return "Teaching hours must be greater than 0.";
    }

    const key = `${tc.year}-${tc.term}`;
    groupedTeachingHours[key] = (groupedTeachingHours[key] || 0) + tc.teachingHours;
  }

  for (const key in groupedTeachingHours) {
    if (groupedTeachingHours[key] !== totalHours) {
      return `Total teaching hours for ${key} do not match the specified total hours.`;
    }
  }
  return null;
};

// Create course in database
const createCourse = async ({ id, name, totalHours, level, taughtCourses }: CourseInput) => {
  return await prisma.course.create({
    data: {
      id,
      name,
      totalHours,
      level,
      taughtCourses: {
        create: taughtCourses.map((taughtCourse) => ({
          teacherId: taughtCourse.teacherId,
          year: taughtCourse.year,
          term: taughtCourse.term,
          teachingHours: taughtCourse.teachingHours,
        })),
      },
    },
  });
};

// Main handler function
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "POST") {
    res.setHeader("Allow", ["POST"]);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  const input = req.body as CourseInput;

  try {
    // Validate input
    if (!validateInput(input)) {
      return res.status(400).json({ error: "Invalid input data." });
    }

    // Check for duplicate course
    if (await checkDuplicateCourse(input.id)) {
      return res.status(400).json({ error: "Course ID already exists." });
    }

    // Validate teachers
    const invalidTeacherId = await validateTeachers(input.taughtCourses);
    if (invalidTeacherId) {
      return res.status(400).json({ error: `Teacher with ID ${invalidTeacherId} does not exist.` });
    }

    // Validate teaching hours
    const hoursError = validateTeachingHours(input.taughtCourses, input.totalHours);
    if (hoursError) {
      return res.status(400).json({ error: hoursError });
    }

    // Create course
    const course = await createCourse(input);
    return res.status(201).json(course);
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "An error occurred while creating the course." });
  }
}
