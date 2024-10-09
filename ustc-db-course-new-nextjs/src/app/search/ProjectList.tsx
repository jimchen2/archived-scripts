import React from "react";

const projectTypes = {
  1: "国家级项目",
  2: "省部级项目",
  3: "市厅级项目",
  4: "企业合作项目",
  5: "其它类型项目",
};

const ProjectList = ({ projects }) => (
  <div>
    <h3 className="text-lg font-semibold">项目</h3>
    {projects.length > 0 ? (
      <ul>
        {projects.map((proj, index) => (
          <li key={index}>
            <h4>{proj.project.name}</h4>
            <p>来源: {proj.project.source}</p>
            <p>项目类型: {projectTypes[proj.project.projectType]}</p>
            <p>总资金: ¥{proj.project.totalFunding}</p>
            <p>开始年份: {proj.project.startYear}</p>
            <p>结束年份: {proj.project.endYear}</p>
            <p>排名: {proj.ranking}</p>
            <p>资金: ¥{proj.funding}</p>
          </li>
        ))}
      </ul>
    ) : (
      <p>没有找到项目</p>
    )}
  </div>
);

export default ProjectList;
