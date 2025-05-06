const express = require("express");
const router = express.Router();
const db = require("../../db");
const { auth, checkSuperadmin } = require("../../middlewares/auth");

// Helper function to convert BigInt to string
const convertBigIntToString = (obj) => {
  for (let key in obj) {
    if (typeof obj[key] === "bigint") {
      obj[key] = obj[key].toString();
    }
  }
  return obj;
};

// Function to validate if a value is an integer
const isValidInteger = (value) => {
  return Number.isInteger(Number(value));
};

// Add a new paper
router.post("/", auth, checkSuperadmin, async (req, res) => {
  const { name, source, year, type, level } = req.body;

  // Validate required fields
  if (!name || !year || !type || !level) {
    return res.status(400).send("All fields are required.");
  }

  // Validate year, type, and level
  const validTypes = [1, 2, 3, 4];
  const validLevels = [1, 2, 3, 4, 5, 6];
  if (
    !isValidInteger(year) ||
    !validTypes.includes(type) ||
    !validLevels.includes(level)
  ) {
    return res.status(400).send("Invalid year, type, or level.");
  }

  try {
    const query =
      "INSERT INTO papers (name, source, year, type, level) VALUES (?, ?, ?, ?, ?)";
    const result = await db.query(query, [name, source, year, type, level]);
    res.status(201).send({ id: result.insertId.toString() }); // Convert BigInt to string
  } catch (err) {
    console.error(err);
    res.status(500).send(err.message);
  }
});

// Update paper details
router.put("/:paperId", auth, checkSuperadmin, async (req, res) => {
  const { paperId } = req.params;
  const { name, source, year, type, level } = req.body;

  // Validate required fields
  if (!name || !year || !type || !level) {
    return res.status(400).send("All fields are required.");
  }

  // Validate year, type, and level
  const validTypes = [1, 2, 3, 4];
  const validLevels = [1, 2, 3, 4, 5, 6];
  if (
    !isValidInteger(year) ||
    !validTypes.includes(type) ||
    !validLevels.includes(level)
  ) {
    return res.status(400).send("Invalid year, type, or level.");
  }

  try {
    const query =
      "UPDATE papers SET name = ?, source = ?, year = ?, type = ?, level = ? WHERE id = ?";
    await db.query(query, [name, source, year, type, level, paperId]);
    res.status(200).send({ message: "Paper updated successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send(err.message);
  }
});

// Get details of a specific paper
router.get("/:paperId", async (req, res) => {
  const { paperId } = req.params;

  try {
    const query = "SELECT * FROM papers WHERE id = ?";
    const results = await db.query(query, [paperId]);

    if (results.length === 0) {
      return res.status(404).send("Paper not found");
    }
    res.status(200).send(convertBigIntToString(results[0])); // Convert BigInt to string
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching paper");
  }
});

// Get all papers
router.get("/", async (req, res) => {
  try {
    const query = "SELECT * FROM papers";
    const results = await db.query(query);
    res.status(200).send(results.map(convertBigIntToString)); // Convert BigInt to string
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching papers");
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
