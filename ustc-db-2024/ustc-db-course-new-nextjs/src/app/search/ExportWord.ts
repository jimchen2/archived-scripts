import { Packer, Document, Paragraph, TextRun } from "docx";
import { saveAs } from "file-saver";

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

export const exportToWord = async (results) => {
  const doc = new Document({
    sections: [
      {
        children: [
          new Paragraph({
            children: [
              new TextRun({
                text: "教学和研究工作量报告",
                bold: true,
                size: 28,
              }),
            ],
          }),
          new Paragraph({
            children: [
              new TextRun({
                text: "论文:",
                bold: true,
                size: 24,
              }),
            ],
          }),
          ...results.publishedPapers.map(paper =>
            new Paragraph({
              children: [
                new TextRun({
                  text: `${paper.paper.name}, ${paper.paper.source}, ${paper.paper.year}, ${paperTypes[paper.paper.type]}, ${paperLevels[paper.paper.level]}, ${paper.ranking}, ${paper.isCorrespondingAuthor ? '是' : '否'}`,
                  size: 22,
                }),
              ],
            })
          ),
          new Paragraph({
            children: [
              new TextRun({
                text: "项目:",
                bold: true,
                size: 24,
              }),
            ],
          }),
          ...results.projectParticipants.map(project =>
            new Paragraph({
              children: [
                new TextRun({
                  text: `${project.project.name}, ${project.project.source}, ${projectTypes[project.project.projectType]}, ${project.project.totalFunding}, ${project.project.startYear}, ${project.project.endYear}, ${project.ranking}, ${project.funding}`,
                  size: 22,
                }),
              ],
            })
          ),
          new Paragraph({
            children: [
              new TextRun({
                text: "课程:",
                bold: true,
                size: 24,
              }),
            ],
          }),
          ...results.taughtCourses.map(course =>
            new Paragraph({
              children: [
                new TextRun({
                  text: `${course.course.name}, ${course.year}, ${terms[course.term]}, ${course.teachingHours}, ${course.course.totalHours}, ${courseLevels[course.course.level]}`,
                  size: 22,
                }),
              ],
            })
          ),
        ],
      },
    ],
  });

  const buffer = await Packer.toBuffer(doc);
  saveAs(
    new Blob([buffer], {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }),
    "Teaching_Research_Report.docx"
  );
};
