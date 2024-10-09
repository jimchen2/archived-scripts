const db = require("../../db");

const getTeacherInfo = async (teacherId) => {
  const teacherQuery = `
    SELECT 
      id, 
      name, 
      CASE gender
        WHEN 1 THEN '男'
        WHEN 2 THEN '女'
        WHEN 3 THEN '其他'
      END AS gender,
      CASE title
        WHEN 1 THEN '博士后'
        WHEN 2 THEN '助教'
        WHEN 3 THEN '讲师'
        WHEN 4 THEN '副教授'
        WHEN 5 THEN '特任教授'
        WHEN 6 THEN '教授'
        WHEN 7 THEN '助理研究员'
        WHEN 8 THEN '特任副研究员'
        WHEN 9 THEN '副研究员'
        WHEN 10 THEN '特任研究员'
        WHEN 11 THEN '研究员'
      END AS title
    FROM teachers 
    WHERE id = ?
  `;
  const [result] = await db.query(teacherQuery, [teacherId]);
  return result;
};

const getPapers = async (teacherId) => {
  const papersQuery = `
    SELECT 
      p.name, 
      p.source, 
      p.year, 
      CASE p.type
        WHEN 1 THEN 'full paper'
        WHEN 2 THEN 'short paper'
        WHEN 3 THEN 'poster paper'
        WHEN 4 THEN 'demo paper'
      END AS type,
      CASE p.level
        WHEN 1 THEN 'CCF-A'
        WHEN 2 THEN 'CCF-B'
        WHEN 3 THEN 'CCF-C'
        WHEN 4 THEN '中文CCF-A'
        WHEN 5 THEN '中文CCF-B'
        WHEN 6 THEN '无级别'
      END AS level,
      pp.ranking, 
      pp.is_corresponding_author
    FROM papers p
    JOIN published_papers pp ON p.id = pp.paper_id
    WHERE pp.teacher_id = ?
  `;
  const result = await db.query(papersQuery, [teacherId]);
  return result;
};

const getProjects = async (teacherId) => {
  const projectsQuery = `
    SELECT 
      pr.name, 
      pr.source, 
      CASE pr.project_type
        WHEN 1 THEN '国家级项目'
        WHEN 2 THEN '省部级项目'
        WHEN 3 THEN '市厅级项目'
        WHEN 4 THEN '企业合作项目'
        WHEN 5 THEN '其它类型项目'
      END AS project_type,
      pr.total_funding, 
      pr.start_year, 
      pr.end_year, 
      pp.funding, 
      pp.ranking
    FROM projects pr
    JOIN project_participants pp ON pr.id = pp.project_id
    WHERE pp.teacher_id = ?
  `;
  const result = await db.query(projectsQuery, [teacherId]);
  return result;
};

const getCourses = async (teacherId) => {
    const coursesQuery = `
      SELECT 
        c.id as course_id, 
        c.name, 
        c.total_hours, 
        CASE c.level
          WHEN 1 THEN '本科生课程'
          WHEN 2 THEN '研究生课程'
        END AS level,
        tc.year, 
        CASE tc.term
          WHEN 1 THEN '春季学期'
          WHEN 2 THEN '夏季学期'
          WHEN 3 THEN '秋季学期'
        END AS term,
        tc.teaching_hours
      FROM courses c
      JOIN taught_courses tc ON c.id = tc.course_id
      WHERE tc.teacher_id = ?
    `;
    const results = await db.query(coursesQuery, [teacherId]);
    return results; // Return the whole array
  };
  
module.exports = {
  getTeacherInfo,
  getPapers,
  getProjects,
  getCourses,
};
