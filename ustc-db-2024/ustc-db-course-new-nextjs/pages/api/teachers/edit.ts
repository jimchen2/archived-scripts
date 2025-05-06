// pages/api/teachers/edit.ts


// curl -X PUT http://localhost:3000/api/teachers/edit \
//   -H "Content-Type: application/json" \
//   -d '{
//         "id": "1",
//         "name": "Jane Doe",
//         "gender": "2",
//         "title": "3"
//       }'




import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  console.log("Received request:", req.method);
  console.log("Request body:", req.body);

  if (req.method === "PUT") {
    const { id, name, gender, title } = req.body;

    if (!id || typeof id !== "string") {
      console.log("Invalid ID:", id);
      res.status(400).json({ error: "Invalid ID provided" });
      return;
    }

    console.log("Parsed body:", { id, name, gender, title });

    try {
      const parsedGender = parseInt(gender);
      const parsedTitle = parseInt(title);

      console.log("Parsed gender and title:", { parsedGender, parsedTitle });

      const teacher = await prisma.teacher.update({
        where: { id: id.toString() },
        data: {
          name,
          gender: parsedGender,
          title: parsedTitle,
        },
      });

      console.log("Teacher updated:", teacher);
      res.status(200).json(teacher);
    } catch (error) {
      console.error("Error updating teacher:", error);
      res.status(500).json({ error: "Failed to update teacher" });
    }
  } else {
    console.log("Invalid request method");
    res.status(405).json({ error: "Method not allowed" });
  }
}
