import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  console.log("Received request:", req.method);
  console.log("Request body:", req.body);

  if (req.method === "POST") {
    const { id, name, gender, title } = req.body;

    console.log("Parsed body:", { id, name, gender, title });

    try {
      const parsedGender = parseInt(gender);
      const parsedTitle = parseInt(title);

      console.log("Parsed gender and title:", { parsedGender, parsedTitle });

      // Check for duplicates
      const existingTeacher = await prisma.teacher.findFirst({
        where: {
          OR: [{ id: id.toString() }],
        },
      });

      if (existingTeacher) {
        res
          .status(409)
          .json({ error: "Teacher with the same ID already exists" });
        return;
      }

      const teacher = await prisma.teacher.create({
        data: {
          id: id.toString(),
          name,
          gender: parsedGender,
          title: parsedTitle,
        },
      });

      console.log("Teacher created:", teacher);
      res.status(200).json(teacher);
    } catch (error) {
      console.error("Error creating teacher:", error);
      res.status(500).json({ error: "Failed to create teacher" });
    }
  } else {
    console.log("Invalid request method");
    res.status(405).json({ error: "Method not allowed" });
  }
}
