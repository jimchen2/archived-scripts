// pages/api/teachers/list.ts



// curl -X GET 'http://localhost:3000/api/teachers/list'
// curl -X GET 'http://localhost:3000/api/teachers/list?id=1'



import { NextApiRequest, NextApiResponse } from "next";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  console.log("Received request:", req.method);
  console.log("Request query:", req.query);

  if (req.method === "GET") {
    const { id } = req.query;

    try {
      let teachers;
      if (id) {
        console.log("Searching for ID:", id);
        teachers = await prisma.teacher.findMany({
          where: {
            id: id.toString(),
          },
        });
      } else {
        console.log("Fetching all teachers");
        teachers = await prisma.teacher.findMany();
      }

      console.log("Teachers found:", teachers);
      res.status(200).json(teachers);
    } catch (error) {
      console.error("Error fetching teachers:", error);
      res.status(500).json({ error: "Failed to fetch teachers" });
    }
  } else {
    console.log("Invalid request method");
    res.status(405).json({ error: "Method not allowed" });
  }
}
