const express = require("express");
const router = express.Router();
const db = require("../../db");
const { auth } = require("../../middlewares/auth");

router.post("/", auth, async (req, res) => {
  const { paper_id, ranking, is_corresponding_author } = req.body;
  const teacher_id = req.auth.id;

  try {
    // Check if the paper_id exists in the papers table
    const checkPaperQuery = "SELECT COUNT(*) AS count FROM papers WHERE id = ?";
    const [paperResult] = await db.query(checkPaperQuery, [paper_id]);
    console.log(paperResult);
    const paperCount = paperResult.count;

    if (paperCount === 0) {
      return res.status(400).send("Invalid paper_id");
    }
    // Check if the teacher_id exists in the teachers table
    console.log("Checking teacher_id:", teacher_id);
    console.log("Type of teacher_id:", typeof teacher_id);

    const checkTeacherQuery =
      "SELECT COUNT(*) AS count FROM teachers WHERE id = ?";
    console.log("checkTeacherQuery:", checkTeacherQuery);

    const [teacherResult] = await db.query(checkTeacherQuery, [teacher_id]);
    console.log("teacherResult:", teacherResult);

    const teacherCount = teacherResult.count;
    console.log("teacherCount:", teacherCount);

    if (teacherCount === 0) {
      console.log("Invalid teacher_id:", teacher_id);
      return res.status(400).send("Invalid teacher_id");
    }

    console.log("Valid teacher_id:", teacher_id);

    // Check if the paper already has a corresponding author
    if (is_corresponding_author) {
      const checkCorrespondingAuthorQuery =
        "SELECT COUNT(*) AS count FROM published_papers WHERE paper_id = ? AND is_corresponding_author = 1";
      const [correspondingAuthorResult] = await db.query(
        checkCorrespondingAuthorQuery,
        [paper_id]
      );
      const correspondingAuthorCount = correspondingAuthorResult[0]?.count || 0;

      if (correspondingAuthorCount > 0) {
        return res.status(400).send("Paper already has a corresponding author");
      }
    }

    const checkPublishedPaperQuery =
      "SELECT COUNT(*) AS count FROM published_papers WHERE paper_id = ? AND teacher_id = ?";
    const [publishedPaperResult] = await db.query(checkPublishedPaperQuery, [
      paper_id,
      teacher_id,
    ]);
    const publishedPaperCount = publishedPaperResult.count;

    if (publishedPaperCount > 0) {
      return res
        .status(400)
        .send("Paper is already associated with the teacher");
    }

    // Insert the published_paper record
    const insertPublishedPaperQuery =
      "INSERT INTO published_papers (paper_id, teacher_id, ranking, is_corresponding_author) VALUES (?, ?, ?, ?)";
    await db.query(insertPublishedPaperQuery, [
      paper_id,
      teacher_id,
      ranking,
      is_corresponding_author,
    ]);

    res.status(201).send({ message: "Paper added successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error adding paper");
  }
});


// Delete a paper for a teacher
router.delete("/:paperId", auth, async (req, res) => {
  const { paperId } = req.params;
  const teacher_id = req.auth.id;

  try {
    // Delete the published_paper record to remove the teacher from the paper
    const deletePublishedPaperQuery =
      "DELETE FROM published_papers WHERE paper_id = ? AND teacher_id = ?";
    await db.query(deletePublishedPaperQuery, [paperId, teacher_id]);

    res
      .status(200)
      .send({ message: "Teacher removed from the paper successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).send("Error removing teacher from the paper");
  }
});

// Get all papers for a teacher
router.get("/", auth, async (req, res) => {
  const teacher_id = req.auth.id;

  try {
    const query = `
      SELECT
        p.id,
        p.name,
        p.source,
        p.year,
        p.type,
        p.level,
        pp.ranking,
        pp.is_corresponding_author
      FROM
        papers p
        JOIN published_papers pp ON p.id = pp.paper_id
      WHERE
        pp.teacher_id = ?
    `;
    const results = await db.query(query, [teacher_id]);
    res.status(200).send(results);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching papers");
  }
});

// Get a specific paper by ID for a teacher
router.get("/:paperId", auth, async (req, res) => {
  const { paperId } = req.params;
  const teacher_id = req.auth.id;

  try {
    const query = `
      SELECT
        p.id,
        p.name,
        p.source,
        p.year,
        p.type,
        p.level,
        pp.ranking,
        pp.is_corresponding_author
      FROM
        papers p
        JOIN published_papers pp ON p.id = pp.paper_id
      WHERE
        p.id = ?
        AND pp.teacher_id = ?
    `;
    const results = await db.query(query, [paperId, teacher_id]);

    if (results.length === 0) {
      return res.status(404).send("Paper not found");
    }

    res.status(200).send(results[0]);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching paper");
  }
});

module.exports = router;

















// Update a paper for a teacher
router.put("/:paperId", auth, async (req, res) => {
  console.log("Updating a paper for a teacher");
  const { paperId } = req.params;
  const { ranking, is_corresponding_author } = req.body;
  const teacher_id = req.auth.id;

  console.log("Paper ID:", paperId);
  console.log("Type of Paper ID:", typeof paperId);
  console.log("Ranking:", ranking);
  console.log("Type of Ranking:", typeof ranking);
  console.log("Is Corresponding Author:", is_corresponding_author);
  console.log("Type of Is Corresponding Author:", typeof is_corresponding_author);
  console.log("Teacher ID:", teacher_id);
  console.log("Type of Teacher ID:", typeof teacher_id);

  try {
    // Check if the paper exists for the teacher
    const checkPaperQuery =
      "SELECT COUNT(*) AS count FROM published_papers WHERE paper_id = ? AND teacher_id = ?";
    console.log("Check Paper Query:", checkPaperQuery);

    const [paperResult] = await db.query(checkPaperQuery, [
      paperId,
      teacher_id,
    ]);
    console.log("Paper Result:", paperResult);
    console.log("Type of Paper Result:", typeof paperResult);
    console.log("Paper Result Keys:", Object.keys(paperResult));

    const paperCount = paperResult.count;
    console.log("Paper Count:", paperCount);
    console.log("Type of Paper Count:", typeof paperCount);

    if (paperCount === 0) {
      console.log("Paper not found for the teacher");
      return res.status(404).send("Paper not found for the teacher");
    }

    // Update the published_paper record
    const updatePublishedPaperQuery =
      "UPDATE published_papers SET ranking = ?, is_corresponding_author = ? WHERE paper_id = ? AND teacher_id = ?";
    console.log("Update Published Paper Query:", updatePublishedPaperQuery);

    await db.query(updatePublishedPaperQuery, [
      ranking,
      is_corresponding_author,
      paperId,
      teacher_id,
    ]);
    console.log("Published Paper Record Updated");

    res.status(200).send({ message: "Paper updated successfully" });
    console.log("Response Sent: Paper updated successfully");
  } catch (err) {
    console.error("Error updating paper:", err);
    console.error("Error Stack:", err.stack);
    res.status(500).send("Error updating paper");
  }
});