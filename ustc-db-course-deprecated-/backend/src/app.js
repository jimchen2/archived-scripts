const express = require("express");
const cors = require("cors");
require("dotenv").config(); // Ensure this is at the top to load environment variables

const app = express();
const { auth, handleAuthErrors } = require("./middlewares/auth");

// Ensure database initialization
const initDB = require("./init-db");

const teachersRouter = require("./routes/admin/teachers");
const papersRouter = require("./routes/admin/papers");
const projectsRouter = require("./routes/admin/projects");
const coursesRouter = require("./routes/admin/courses");

const teacherCourses = require("./routes/teacher/courses");
const teacherPapers = require("./routes/teacher/papers");
const teacherExport = require("./routes/teacher/export");

const loginRouter = require("./routes/login");


  const searchyear = require("./routes/searchyear");


// Middleware to parse JSON requests
app.use(express.json());

// Enable CORS for all routes and origins
const corsOptions = {
  origin: process.env.FRONTEND_URL,
  credentials: true,
};

app.use(cors(corsOptions));

// Use the routers
app.use("/teachers", teachersRouter);
app.use("/papers", papersRouter);
app.use("/projects", projectsRouter);

app.use("/courses", coursesRouter);
app.use("/login", loginRouter);
app.use("/teachercourses", teacherCourses);
app.use("/teacherpapers", teacherPapers);
app.use("/teacherexport", teacherExport);


app.use("/search", searchyear);

// Handle authentication errors
app.use(handleAuthErrors);

async function initializeApp() {
  try {
    await initDB(); // Initialize the database
    return app;
  } catch (error) {
    console.error("Failed to initialize database:", error);
    throw error;
  }
}

module.exports = initializeApp;
