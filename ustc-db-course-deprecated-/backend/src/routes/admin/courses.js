const express = require("express");
const router = express.Router();
const db = require("../../db");
const { auth, checkSuperadmin } = require("../../middlewares/auth");

// Add a new course
router.post("/", auth, checkSuperadmin, async (req, res) => {
  const { id, name, total_hours, level } = req.body;

  // Validate level
  const validLevels = [1, 2];
  if (!validLevels.includes(level)) {
    return res.status(400).send("Invalid course level");
  }

  try {
    const query =
      "INSERT INTO courses (id, name, total_hours, level) VALUES (?, ?, ?, ?)";
    await db.query(query, [id, name, total_hours, level]);
    res.status(201).send({ id });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error creating course");
  }
});

// Update course details
router.put("/:courseId", auth, checkSuperadmin, async (req, res) => {
  const { courseId } = req.params;
  const { name, total_hours, level } = req.body;

  // Validate level
  const validLevels = [1, 2];
  if (!validLevels.includes(level)) {
    return res.status(400).send("Invalid course level");
  }

  try {
    const query =
      "UPDATE courses SET name = ?, total_hours = ?, level = ? WHERE id = ?";
    await db.query(query, [name, total_hours, level, courseId]);
    res.status(200).send({ message: "Course updated successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error updating course");
  }
});


// Get details of a specific course
router.get("/:courseId", async (req, res) => {
  const { courseId } = req.params;

  try {
    const query = "SELECT * FROM courses WHERE id = ?";
    const results = await db.query(query, [courseId]);

    if (results.length === 0) {
      return res.status(404).send("Course not found");
    }
    res.status(200).send(results[0]);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching course");
  }
});

// Get all courses
router.get("/", async (req, res) => {
  try {
    const query = "SELECT * FROM courses";
    const results = await db.query(query);
    res.status(200).send(results);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching courses");
  }
});




router.delete("/:courseId", auth, checkSuperadmin, async (req, res) => {
  const { courseId } = req.params;

  let connection;
  try {
    // Get a connection from the pool
    connection = await db.getConnection();

    // Start a transaction
    await connection.beginTransaction();

    // Delete the associated records in the taught_courses table
    const deleteAssociatedRecordsQuery = "DELETE FROM taught_courses WHERE course_id = ?";
    await connection.query(deleteAssociatedRecordsQuery, [courseId]);

    // Delete the course
    const deleteCourseQuery = "DELETE FROM courses WHERE id = ?";
    await connection.query(deleteCourseQuery, [courseId]);

    // Commit the transaction
    await connection.commit();

    res.status(200).send({ message: "Course deleted successfully" });
  } catch (err) {
    console.error(err);

    // Rollback the transaction if an error occurs
    if (connection) {
      await connection.rollback();
    }

    res.status(500).send("Error deleting course");
  } finally {
    // Release the connection back to the pool
    if (connection) {
      await connection.release();
    }
  }
});

module.exports = router;
