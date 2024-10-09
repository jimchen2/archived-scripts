import React from "react";
import { Table, Button } from "react-bootstrap";

const typeMapping = {
  1: "全文论文 (Full Paper)",
  2: "短文论文 (Short Paper)",
  3: "海报论文 (Poster Paper)",
  4: "演示论文 (Demo Paper)",
};

const levelMapping = {
  1: "CCF-A",
  2: "CCF-B",
  3: "CCF-C",
  4: "中文CCF-A (Chinese CCF-A)",
  5: "中文CCF-B (Chinese CCF-B)",
  6: "无级别 (No Level)",
};

const PaperTable = ({ papers, onDeletePaper }) => {
  console.log(papers);
  return (
    <div>
      <h2>论文列表 (Paper List)</h2>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>论文ID (Paper ID)</th>
            <th>论文名称 (Name)</th>
            <th>发表源 (Source)</th>
            <th>发表年份 (Year)</th>
            <th>类型 (Type)</th>
            <th>级别 (Level)</th>
            <th>操作 (Action)</th>
          </tr>
        </thead>
        <tbody>
          {papers.length > 0 ? (
            papers.map((paper) => (
              <tr key={paper.paperId}>
                <td>{paper.id}</td>
                <td>{paper.name}</td>
                <td>{paper.source}</td>
                <td>{paper.year}</td>
                <td>{typeMapping[paper.type]}</td>
                <td>{levelMapping[paper.level]}</td>
                <td>
                  <Button
                    variant="danger"
                    onClick={() => onDeletePaper(paper.paperId)}
                  >
                    删除 (Delete)
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="7" className="text-center">
                No papers available
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </div>
  );
};

export default PaperTable;
