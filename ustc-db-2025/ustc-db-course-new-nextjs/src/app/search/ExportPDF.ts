import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

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

const loadFont = async (url) => {
  const response = await fetch(url);
  const fontBlob = await response.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(fontBlob);
  });
};

export const exportToPDF = async (results) => {
  const doc = new jsPDF();

  // Load the font file and convert to base64
  const fontData = await loadFont('/fonts/NotoSansSC-Regular.ttf');

  // Add the custom font
  // @ts-ignore
  doc.addFileToVFS("NotoSansSC-Regular.ttf", fontData.split(',')[1]);
  doc.addFont("NotoSansSC-Regular.ttf", "NotoSansSC", "normal");
  doc.setFont("NotoSansSC");

  doc.text("教学和研究工作量报告", 10, 10);

  const autoTableOptions = {
    headStyles: { font: "NotoSansSC", fontStyle: "normal" },
    bodyStyles: { font: "NotoSansSC", fontStyle: "normal" },
  };

  // @ts-ignore
  autoTable(doc, {
    startY: 20,
    head: [['论文名称', '来源', '年份', '类型', '级别', '排名', '通讯作者']],
    body: results.publishedPapers.map(paper => [
      paper.paper.name,
      paper.paper.source,
      paper.paper.year,
      paperTypes[paper.paper.type],
      paperLevels[paper.paper.level],
      paper.ranking,
      paper.isCorrespondingAuthor ? '是' : '否'
    ]),
    ...autoTableOptions
  });

// @ts-ignore
  autoTable(doc, {
    // @ts-ignore
    startY: doc.lastAutoTable.finalY + 10,
    head: [['项目名称', '来源', '项目类型', '总资金', '开始年份', '结束年份', '排名', '资金']],
    body: results.projectParticipants.map(project => [
      project.project.name,
      project.project.source,
      projectTypes[project.project.projectType],
      project.project.totalFunding,
      project.project.startYear,
      project.project.endYear,
      project.ranking,
      project.funding
    ]),
    ...autoTableOptions
  });
// @ts-ignore
  autoTable(doc, {
  // @ts-ignore 
    startY: doc.lastAutoTable.finalY + 10,
    head: [['课程名称', '年份', '学期', '教学时长', '总时长', '课程级别']],
    body: results.taughtCourses.map(course => [
      course.course.name,
      course.year,
      terms[course.term],
      course.teachingHours,
      course.course.totalHours,
      courseLevels[course.course.level]
    ]),
    ...autoTableOptions
  });

  doc.save('Teaching_Research_Report.pdf');
};
