// pages/api/teachers/delete.ts


// curl -X DELETE http://localhost:3000/api/teachers/delete \
//   -H "Content-Type: application/json" \
//   -d '{
//         "id": "1"
//       }'


// pages/api/teachers/delete.ts

import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  console.log("Received request:", req.method);
  console.log("Request body:", req.body);

  if (req.method === "DELETE") {
    const { id } = req.body;

    if (!id || typeof id !== "string") {
      console.log("Invalid ID:", id);
      res.status(400).json({ error: "Invalid ID provided" });
      return;
    }

    console.log("Parsed body:", { id });

    try {
      // Delete all associated records
      await prisma.publishedPaper.deleteMany({
        where: {
          teacherId: id,
        },
      });

      await prisma.projectParticipant.deleteMany({
        where: {
          teacherId: id,
        },
      });

      await prisma.taughtCourse.deleteMany({
        where: {
          teacherId: id,
        },
      });

      // Delete the teacher
      const teacher = await prisma.teacher.delete({
        where: {
          id,
        },
      });

      console.log("Teacher deleted:", teacher);
      res
        .status(200)
        .json({ message: "Teacher and associated records deleted successfully", teacher });
    } catch (error) {
      console.error("Error deleting teacher:", error);
      res.status(500).json({ error: "Failed to delete teacher" });
    }
  } else {
    console.log("Invalid request method");
    res.status(405).json({ error: "Method not allowed" });
  }
}
