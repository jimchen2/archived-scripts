const mariadb = require('mariadb');
require("dotenv").config();

const pool = mariadb.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  multipleStatements: true  // Enable multiple statements
});

async function testConnection() {
  let connection;
  try {
    connection = await pool.getConnection();
    console.log("Connected to the MariaDB database.");
  } catch (err) {
    console.error("Error connecting to the database:", err);
  } finally {
    if (connection) await connection.release();
  }
}

// testConnection();

module.exports = pool;
