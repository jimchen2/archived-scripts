// routes/login.js
const express = require("express");
const router = express.Router();
const db = require("../db");
const jwt = require("jsonwebtoken");
const argon2 = require("argon2");

require("dotenv").config();
const secret = process.env.JWT_SECRET;

router.post("/", async (req, res) => {
  const { id, password } = req.body;

  const query = "SELECT password_hash FROM teacher_password WHERE teacher_id = ?";

  try {
    const connection = await db.getConnection();
    const results = await connection.query(query, [id]);
    connection.release();

    if (results.length === 0) {
      return res.status(401).send("Invalid credentials");
    }

    const passwordHash = results[0].password_hash;
    const isValid = await argon2.verify(passwordHash, password);

    if (!isValid) {
      return res.status(401).send("Invalid credentials");
    }

    const token = jwt.sign({ id }, secret, { expiresIn: "1h" });
    res.status(200).json({ token });
  } catch (err) {
    console.error("Error logging in:", err);
    res.status(500).send("Error logging in");
  }
});

module.exports = router;
