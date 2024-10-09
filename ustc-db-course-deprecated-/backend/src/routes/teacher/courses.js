const express = require("express");
const router = express.Router();
const db = require("../../db");
const { auth } = require("../../middlewares/auth");

// Add a taught course for a teacher
router.post("/", auth, async (req, res) => {
  const { course_id, year, term, teaching_hours } = req.body;
  const teacher_id = req.auth.id;

  // Validate term
  const validTerms = [1, 2, 3];
  if (!validTerms.includes(term)) {
    return res.status(400).send("Invalid term");
  }

  try {
    // Check if the course exists in the courses table
    const checkCourseQuery = "SELECT id FROM courses WHERE id = ?";
    const [courseExists] = await db.query(checkCourseQuery, [course_id]);

    if (!courseExists) {
      return res.status(400).send("Invalid course ID");
    }
    // Check if a record with the same course_id and teacher_id already exists
    const checkExistingRecordQuery =
      "SELECT * FROM taught_courses WHERE course_id = ? AND teacher_id = ?";
    const existingRecords = await db.query(checkExistingRecordQuery, [
      course_id,
      teacher_id,
    ]);

    if (existingRecords.length > 0) {
      // Update the existing record
      const updateQuery =
        "UPDATE taught_courses SET year = ?, term = ?, teaching_hours = ? WHERE course_id = ? AND teacher_id = ?";
      await db.query(updateQuery, [
        year,
        term,
        teaching_hours,
        course_id,
        teacher_id,
      ]);
      res.status(200).send({ message: "Taught course updated successfully" });
    } else {
      // Insert a new record
      const insertQuery =
        "INSERT INTO taught_courses (course_id, teacher_id, year, term, teaching_hours) VALUES (?, ?, ?, ?, ?)";
      await db.query(insertQuery, [
        course_id,
        teacher_id,
        year,
        term,
        teaching_hours,
      ]);
      res.status(201).send({ message: "Taught course added successfully" });
    }
  } catch (err) {
    console.error(err);
    res.status(500).send("Error adding/updating taught course");
  }
});

// Update a taught course for a teacher
router.put("/:courseId", auth, async (req, res) => {
  const { courseId } = req.params;
  const { year, term, teaching_hours } = req.body;
  const teacher_id = req.auth.id;

  // Validate term
  const validTerms = [1, 2, 3];
  if (!validTerms.includes(term)) {
    return res.status(400).send("Invalid term");
  }

  try {
    // Check if the course exists in the courses table
    const checkCourseQuery = "SELECT id FROM courses WHERE id = ?";
    const [courseExists] = await db.query(checkCourseQuery, [courseId]);

    if (!courseExists) {
      return res.status(400).send("Invalid course ID");
    }

    const query =
      "UPDATE taught_courses SET year = ?, term = ?, teaching_hours = ? WHERE course_id = ? AND teacher_id = ?";
    await db.query(query, [year, term, teaching_hours, courseId, teacher_id]);
    res.status(200).send({ message: "Taught course updated successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error updating taught course");
  }
});

// Delete a taught course for a teacher
router.delete("/:courseId", auth, async (req, res) => {
  const { courseId } = req.params;
  const teacher_id = req.auth.id;

  try {
    const query =
      "DELETE FROM taught_courses WHERE course_id = ? AND teacher_id = ?";
    await db.query(query, [courseId, teacher_id]);
    res.status(200).send({ message: "Taught course deleted successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error deleting taught course");
  }
});

// Get all taught courses for a teacher
router.get("/", auth, async (req, res) => {
  const teacher_id = req.auth.id;

  try {
    const query = "SELECT * FROM taught_courses WHERE teacher_id = ?";
    const results = await db.query(query, [teacher_id]);
    res.status(200).send(results);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching taught courses");
  }
});

// Get a specific taught course by ID for a teacher
router.get("/:courseId", auth, async (req, res) => {
  const { courseId } = req.params;
  const teacher_id = req.auth.id;

  try {
    const query = `
      SELECT 
        tc.course_id,
        tc.teacher_id,
        tc.year,
        tc.term,
        tc.teaching_hours,
        c.name AS course_name,
        c.total_hours AS course_total_hours,
        c.level AS course_level
      FROM 
        taught_courses tc
        JOIN courses c ON tc.course_id = c.id
      WHERE 
        tc.course_id = ? 
        AND tc.teacher_id = ?
    `;
    const results = await db.query(query, [courseId, teacher_id]);

    if (results.length === 0) {
      return res.status(404).send("Taught course not found");
    }

    const taughtCourse = {
      course_id: results[0].course_id,
      teacher_id: results[0].teacher_id,
      year: results[0].year,
      term: results[0].term,
      teaching_hours: results[0].teaching_hours,
      course: {
        name: results[0].course_name,
        total_hours: results[0].course_total_hours,
        level: results[0].course_level,
      },
    };

    res.status(200).send(taughtCourse);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching taught course");
  }
});

module.exports = router;
