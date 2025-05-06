const fs = require("fs");
const argon2 = require("argon2");
require("dotenv").config();
const pool = require("./db");

async function initializeDatabase() {
  let connection;
  try {
    connection = await pool.getConnection();
    console.log("Connected to the MariaDB database.");
    // Drop all tables in the existing database
    console.log("Dropping tables in existing database...");
    try {
      await connection.query("USE teacher_management;");
      await connection.query("SET FOREIGN_KEY_CHECKS = 0;");
      await connection.query(
        "DROP TABLE IF EXISTS teachers, teacher_password, papers, published_papers, projects, project_participants, courses, taught_courses;"
      );
      await connection.query("SET FOREIGN_KEY_CHECKS = 1;");
      console.log("Tables dropped.");
    } catch (error) {
      console.error("Error dropping tables:", error);
    }
  } catch (err) {
    console.error("An error occurred while initializing the database:", err);
  } finally {
    if (connection) connection.release();
  }

  console.log("Initializing database schema...");
  const initSql = fs.readFileSync("src/init.sql", "utf-8");
  await connection.query(initSql);
  console.log("Database schema initialized successfully.");

  // Create the superadmin user
  const superadminId = "-1";
  const superadminPassword = "password";
  const superadminName = "superadmin";
  const superadminGender = 1;
  const superadminTitle = 1;
  const passwordHash = await argon2.hash(superadminPassword);

  await connection.query(
    "INSERT INTO teachers (id, name, gender, title) VALUES (?, ?, ?, ?)",
    [superadminId, superadminName, superadminGender, superadminTitle]
  );
  await connection.query(
    "INSERT INTO teacher_password (teacher_id, password_hash) VALUES (?, ?)",
    [superadminId, passwordHash]
  );
  console.log("Superadmin created successfully.");
}

module.exports = initializeDatabase;
