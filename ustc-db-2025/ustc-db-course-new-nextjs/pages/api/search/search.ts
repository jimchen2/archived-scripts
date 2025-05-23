// pages/api/teachers/[teacherId].ts
import { NextApiRequest, NextApiResponse } from 'next';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Validate query parameters
function validateQueryParams(
  teacherId: unknown,
  startYear: unknown,
  endYear: unknown
): { isValid: boolean; error?: string; start: number; end: number } {
  if (!teacherId) {
    return { isValid: false, error: 'Teacher ID is required', start: 0, end: 0 };
  }

  const start = parseInt(startYear as string) || 0;
  const end = parseInt(endYear as string) || new Date().getFullYear();

  return { isValid: true, start, end };
}

// Fetch teacher data with related information
async function fetchTeacherData(
  teacherId: string,
  start: number,
  end: number
) {
  return prisma.teacher.findUnique({
    where: { id: teacherId },
    include: {
      publishedPapers: {
        include: {
          paper: true,
        },
        where: {
          paper: {
            year: {
              gte: start,
              lte: end,
            },
          },
        },
      },
      projectParticipants: {
        include: {
          project: true,
        },
        where: {
          OR: [
            {
              project: {
                startYear: {
                  gte: start,
                  lte: end,
                },
              },
            },
            {
              project: {
                endYear: {
                  gte: start,
                  lte: end,
                },
              },
            },
          ],
        },
      },
      taughtCourses: {
        include: {
          course: true,
        },
        where: {
          year: {
            gte: start,
            lte: end,
          },
        },
      },
    },
  });
}

// Handle errors
function handleError(error: unknown, res: NextApiResponse): void {
  console.error('Error in /api/teachers/[teacherId]:', error);
  res.status(500).json({ error: 'Internal server error' });
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { teacherId, startYear, endYear } = req.query;

  try {
    // Validate query parameters
    const { isValid, error, start, end } = validateQueryParams(teacherId, startYear, endYear);
    if (!isValid) {
      return res.status(400).json({ error });
    }

    // Fetch teacher data
    const teacher = await fetchTeacherData(teacherId as string, start, end);
    if (!teacher) {
      return res.status(404).json({ error: 'Teacher not found' });
    }

    return res.status(200).json({ teacher });
  } catch (error) {
    handleError(error, res);
  }
}