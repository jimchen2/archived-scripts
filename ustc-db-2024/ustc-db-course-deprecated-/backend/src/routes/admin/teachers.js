const express = require("express");
const router = express.Router();
const db = require("../../db");
const argon2 = require("argon2");
const { auth, checkSuperadmin } = require("../../middlewares/auth");

router.post("/", auth, checkSuperadmin, async (req, res) => {
  const { id, name, gender, title, password } = req.body;

  if (!id || !name || !gender || !title || !password) {
    return res.status(400).send("Missing required fields");
  }

  try {
    const passwordHash = await argon2.hash(password);

    const teacherQuery =
      "INSERT INTO teachers (id, name, gender, title) VALUES (?, ?, ?, ?)";
    await db.query(teacherQuery, [id, name, gender, title]);

    const passwordQuery =
      "INSERT INTO teacher_password (teacher_id, password_hash) VALUES (?, ?)";
    await db.query(passwordQuery, [id, passwordHash]);

    res.status(201).send({ id });
  } catch (err) {
    if (err.code === "ER_DUP_ENTRY") {
      return res.status(409).send("Teacher with this ID already exists");
    }

    console.error(err);
    res.status(500).send("Error creating teacher");
  }
});

router.get("/", auth, checkSuperadmin, async (req, res) => {
  try {
    const query = "SELECT * FROM teachers";
    const results = await db.query(query);
    res.status(200).send(results);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching teachers");
  }
});

router.get("/:id", auth, checkSuperadmin, async (req, res) => {
  const { id } = req.params;

  try {
    const query = "SELECT * FROM teachers WHERE id = ?";
    const results = await db.query(query, [id]);

    if (results.length === 0) {
      return res.status(404).send("Teacher not found");
    }

    res.status(200).send(results);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching teacher");
  }
});

router.put("/:id", auth, checkSuperadmin, async (req, res) => {
  const { id } = req.params;
  const { name, gender, title, password, newId } = req.body;

  if (!name || !gender || !title) {
    return res.status(400).send("Missing required fields");
  }

  try {
    const updateTeacherQuery =
      "UPDATE teachers SET id = COALESCE(?, id), name = ?, gender = ?, title = ? WHERE id = ?";
    await db.query(updateTeacherQuery, [newId, name, gender, title, id]);

    if (password) {
      const passwordHash = await argon2.hash(password);
      const updatePasswordQuery =
        "UPDATE teacher_password SET teacher_id = COALESCE(?, teacher_id), password_hash = ? WHERE teacher_id = ?";
      await db.query(updatePasswordQuery, [newId, passwordHash, id]);
    } else if (newId) {
      const updatePasswordIdQuery =
        "UPDATE teacher_password SET teacher_id = ? WHERE teacher_id = ?";
      await db.query(updatePasswordIdQuery, [newId, id]);
    }

    res.status(200).send({ message: "Teacher updated successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error updating teacher");
  }
});

router.delete("/:id", auth, checkSuperadmin, async (req, res) => {
  const { id } = req.params;

  let connection;
  try {
    // Get a connection from the pool
    connection = await db.getConnection();

    // Start a transaction
    await connection.beginTransaction();

    // Delete associated records in the teacher_password table
    const deletePasswordQuery =
      "DELETE FROM teacher_password WHERE teacher_id = ?";
    await connection.query(deletePasswordQuery, [id]);

    // Delete associated records in the published_papers table
    const deletePublishedPapersQuery =
      "DELETE FROM published_papers WHERE teacher_id = ?";
    await connection.query(deletePublishedPapersQuery, [id]);

    // Delete associated records in the project_participants table
    const deleteProjectParticipantsQuery =
      "DELETE FROM project_participants WHERE teacher_id = ?";
    await connection.query(deleteProjectParticipantsQuery, [id]);

    // Delete associated records in the taught_courses table
    const deleteTaughtCoursesQuery =
      "DELETE FROM taught_courses WHERE teacher_id = ?";
    await connection.query(deleteTaughtCoursesQuery, [id]);

    // Delete the teacher
    const deleteTeacherQuery = "DELETE FROM teachers WHERE id = ?";
    await connection.query(deleteTeacherQuery, [id]);

    // Commit the transaction
    await connection.commit();

    res.status(200).send({ message: "Teacher deleted successfully" });
  } catch (err) {
    console.error(err);

    // Rollback the transaction if an error occurs
    if (connection) {
      await connection.rollback();
    }

    res.status(500).send("Error deleting teacher");
  } finally {
    // Release the connection back to the pool
    if (connection) {
      await connection.release();
    }
  }
});

module.exports = router;
