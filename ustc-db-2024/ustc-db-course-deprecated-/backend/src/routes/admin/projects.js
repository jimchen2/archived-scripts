const express = require("express");
const router = express.Router();
const db = require("../../db");
const { auth, checkSuperadmin } = require("../../middlewares/auth");

router.post("/", auth, checkSuperadmin, async (req, res) => {
  const {
    id,
    name,
    source,
    project_type,
    total_funding,
    start_year,
    end_year,
  } = req.body;

  // Validate project type
  const validTypes = [1, 2, 3, 4, 5];
  if (!validTypes.includes(project_type)) {
    return res.status(400).send("Invalid project type");
  }

  try {
    const query =
      "INSERT INTO projects (id, name, source, project_type, total_funding, start_year, end_year) VALUES (?, ?, ?, ?, ?, ?, ?)";
    const values = [
      id,
      name,
      source,
      project_type,
      parseFloat(total_funding),
      parseInt(start_year),
      parseInt(end_year),
    ];

    await db.query(query, values);
    res.status(201).send({ id });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error creating project");
  }
});

router.get("/:id", async (req, res) => {
  const { id } = req.params;

  try {
    const query = "SELECT * FROM projects WHERE id = ?";
    const results = await db.query(query, [id]);

    console.log("Results type:", typeof results);
    console.log("Results:", results);

    if (results.length === 0) {
      res.status(404).send("Project not found");
    } else {
      res.status(200).send(results);
    }
  } catch (err) {
    console.error("Database error:", err);
    res.status(500).send("Error fetching project");
  }
});
router.get("/", async (req, res) => {
  try {
    const query = "SELECT * FROM projects";
    const results = await db.query(query);
    res.status(200).send(results);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching projects");
  }
});

router.put("/:id", auth, checkSuperadmin, async (req, res) => {
  const { id } = req.params;
  const { name, source, project_type, total_funding, start_year, end_year } =
    req.body;

  // Validate project type
  const validTypes = [1, 2, 3, 4, 5];
  if (!validTypes.includes(project_type)) {
    return res.status(400).send("Invalid project type");
  }

  try {
    const updateQuery =
      "UPDATE projects SET name = ?, source = ?, project_type = ?, total_funding = ?, start_year = ?, end_year = ? WHERE id = ?";
    const values = [
      name,
      source,
      project_type,
      total_funding,
      start_year,
      end_year,
      id,
    ];

    await db.query(updateQuery, values);
    res.status(200).send({ message: "Project updated successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error updating project");
  }
});

// Delete a paper
router.delete("/:paperId", auth, checkSuperadmin, async (req, res) => {
  const { paperId } = req.params;

  let connection;
  try {
    // Get a connection from the pool
    connection = await db.getConnection();

    // Start a transaction
    await connection.beginTransaction();

    // Delete the associated records in the published_papers table
    const deleteAssociatedRecordsQuery =
      "DELETE FROM published_papers WHERE paper_id = ?";
    await connection.query(deleteAssociatedRecordsQuery, [paperId]);

    // Delete the paper
    const deletePaperQuery = "DELETE FROM papers WHERE id = ?";
    await connection.query(deletePaperQuery, [paperId]);

    // Commit the transaction
    await connection.commit();

    res.status(200).send({ message: "Paper deleted successfully" });
  } catch (err) {
    console.error(err);

    // Rollback the transaction if an error occurs
    if (connection) {
      await connection.rollback();
    }

    res.status(500).send(err.message);
  } finally {
    // Release the connection back to the pool
    if (connection) {
      await connection.release();
    }
  }
});
module.exports = router;
