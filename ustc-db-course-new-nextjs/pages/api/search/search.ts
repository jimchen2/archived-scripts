import { NextApiRequest, NextApiResponse } from 'next';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { teacherId, startYear, endYear } = req.query;

  if (!teacherId) {
    return res.status(400).json({ error: 'Teacher ID is required' });
  }

  const start = parseInt(startYear as string) || 0;
  const end = parseInt(endYear as string) || new Date().getFullYear();

  try {
    // Fetch teacher information
    const teacher = await prisma.teacher.findUnique({
      where: { id: teacherId as string },
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

    if (!teacher) {
      return res.status(404).json({ error: 'Teacher not found' });
    }

    return res.status(200).json({ teacher });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
