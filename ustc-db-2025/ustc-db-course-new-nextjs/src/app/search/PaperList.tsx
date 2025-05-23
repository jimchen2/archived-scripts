import React from "react";

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

const PaperList = ({ papers }) => (
  <div>
    <h3 className="text-lg font-semibold">论文</h3>
    {papers.length > 0 ? (
      <ul>
        {papers.map((pub, index) => (
          <li key={index}>
            <h4>{pub.paper.name}</h4>
            <p>来源: {pub.paper.source}</p>
            <p>年份: {pub.paper.year}</p>
            <p>类型: {paperTypes[pub.paper.type]}</p>
            <p>级别: {paperLevels[pub.paper.level]}</p>
            <p>排名: {pub.ranking}</p>
            <p>通讯作者: {pub.isCorrespondingAuthor ? "是" : "否"}</p>
          </li>
        ))}
      </ul>
    ) : (
      <p>没有找到论文</p>
    )}
  </div>
);

export default PaperList;
