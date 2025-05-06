const express = require("express");
const router = express.Router();
const { getTeacherInfo, getPapers, getProjects, getCourses } = require("./reportController");
const { auth } = require("../../middlewares/auth");

// Generate a report of a teacher's teaching and research workload
router.get("/report", auth, async (req, res) => {
  const teacherId = req.auth.id;

  try {
    const teacherResult = await getTeacherInfo(teacherId);
    const papersResult = await getPapers(teacherId);
    const projectsResult = await getProjects(teacherId);
    const coursesResult = await getCourses(teacherId);

    // Create the report object
    const report = {
      teacher: teacherResult,
      papers: papersResult,
      projects: projectsResult,
      courses: coursesResult,
    };

    res.status(200).json(report);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error generating report");
  }
});

module.exports = router;
