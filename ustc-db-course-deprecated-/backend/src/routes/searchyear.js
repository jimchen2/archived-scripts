const express = require("express");
const router = express.Router();
const db = require("../db");

// Search for teacher's teaching and research information
router.get("/:teacherId/:startYear-:endYear", async (req, res) => {
  const { teacherId, startYear, endYear } = req.params;

  try {
    // Query to retrieve teacher's information
    const teacherQuery = "SELECT * FROM teachers WHERE id = ?";
    const teacherResults = await db.query(teacherQuery, [teacherId]);

    if (teacherResults.length === 0) {
      return res.status(404).send("Teacher not found");
    }

    const teacher = teacherResults[0];

    // Query to retrieve published papers
    const papersQuery = `
      SELECT papers.name, papers.source, papers.year, papers.type, papers.level
      FROM papers
      INNER JOIN published_papers ON papers.id = published_papers.paper_id
      WHERE published_papers.teacher_id = ? AND papers.year BETWEEN ? AND ?
    `;
    const papersResults = await db.query(papersQuery, [teacherId, startYear, endYear]);

    // Query to retrieve project participations
    const projectsQuery = `
      SELECT projects.name, projects.source, projects.project_type, projects.total_funding,
             projects.start_year, projects.end_year
      FROM projects
      INNER JOIN project_participants ON projects.id = project_participants.project_id
      WHERE project_participants.teacher_id = ? AND (projects.start_year BETWEEN ? AND ? OR projects.end_year BETWEEN ? AND ?)
    `;
    const projectsResults = await db.query(projectsQuery, [teacherId, startYear, endYear, startYear, endYear]);

    // Query to retrieve taught courses
    const coursesQuery = `
      SELECT courses.name, courses.total_hours, courses.level, taught_courses.year, taught_courses.term,
             taught_courses.teaching_hours
      FROM courses
      INNER JOIN taught_courses ON courses.id = taught_courses.course_id
      WHERE taught_courses.teacher_id = ? AND taught_courses.year BETWEEN ? AND ?
    `;
    const coursesResults = await db.query(coursesQuery, [teacherId, startYear, endYear]);

    // Prepare the response object
    const response = {
      teacher: teacher,
      papers: papersResults,
      projects: projectsResults,
      courses: coursesResults,
    };

    res.status(200).send(response);
  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching teacher's information");
  }
});

module.exports = router;