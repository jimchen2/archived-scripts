import * as XLSX from "xlsx";

const paperTypes = {
  1: "full paper",
  2: "short paper",
  3: "poster paper",
  4: "demo paper",
};

const paperLevels = {
  1: "CCF-A",
  2: "CCF-B",
  3: "CCF-C",
  4: "中文CCF-A",
  5: "中文CCF-B",
  6: "无级别",
};

const projectTypes = {
  1: "国家级项目",
  2: "省部级项目",
  3: "市厅级项目",
  4: "企业合作项目",
  5: "其它类型项目",
};

const terms = {
  1: "春季学期",
  2: "夏季学期",
  3: "秋季学期",
};

const courseLevels = {
  1: "本科生课程",
  2: "研究生课程",
};

export const exportToExcel = (results) => {
  // Create worksheets for papers, projects, and courses
  const papersSheet = XLSX.utils.json_to_sheet(
    results.publishedPapers.map((paper) => ({
      "论文名称": paper.paper.name,
      "来源": paper.paper.source,
      "年份": paper.paper.year,
      "类型": paperTypes[paper.paper.type],
      "级别": paperLevels[paper.paper.level],
      "排名": paper.ranking,
      "通讯作者": paper.isCorrespondingAuthor ? "是" : "否",
    }))
  );

  const projectsSheet = XLSX.utils.json_to_sheet(
    results.projectParticipants.map((project) => ({
      "项目名称": project.project.name,
      "来源": project.project.source,
      "项目类型": projectTypes[project.project.projectType],
      "总资金": project.project.totalFunding,
      "开始年份": project.project.startYear,
      "结束年份": project.project.endYear,
      "排名": project.ranking,
      "资金": project.funding,
    }))
  );

  const coursesSheet = XLSX.utils.json_to_sheet(
    results.taughtCourses.map((course) => ({
      "课程名称": course.course.name,
      "年份": course.year,
      "学期": terms[course.term],
      "教学时长": course.teachingHours,
      "总时长": course.course.totalHours,
      "课程级别": courseLevels[course.course.level],
    }))
  );

  // Create a new workbook and add the sheets
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, papersSheet, "Papers");
  XLSX.utils.book_append_sheet(workbook, projectsSheet, "Projects");
  XLSX.utils.book_append_sheet(workbook, coursesSheet, "Courses");

  // Export the workbook to a file
  XLSX.writeFile(workbook, "Teaching_Research_Report.xlsx");
};
