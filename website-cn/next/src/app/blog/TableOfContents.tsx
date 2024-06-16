import React from "react";

interface TOCProps {
  headings: { id: string; text: string; tagName: string }[];
}

interface TreeNode {
  id: string;
  text: string;
  tagName: string;
  children: TreeNode[];
}

const buildTree = (headings: TOCProps["headings"]): TreeNode[] => {
  const tree: TreeNode[] = [];
  let currentParent: TreeNode | null = null;

  for (const heading of headings) {
    if (heading.tagName !== "H2") {
      continue;
    }

    const node: TreeNode = {
      id: heading.id,
      text: heading.text,
      tagName: heading.tagName,
      children: [],
    };

    tree.push(node);
    currentParent = node;
  }

  return tree;
};

const TableOfContents: React.FC<TOCProps> = ({ headings }) => {
  const tree = buildTree(headings);

  const handleLinkClick = (
    event: React.MouseEvent<HTMLAnchorElement, MouseEvent>,
    id: string
  ) => {
    event.preventDefault(); // Prevent default anchor behavior
    const element = document.getElementById(id);
    if (element) {
      const offset = 110; // Adjust this value to the offset you need
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.scrollY - offset;

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      });
    }
  };

  const renderTree = (nodes: TreeNode[], depth = 0) => {
    return (
      <ul className={`pl-${depth * 4}`}>
        {nodes.map((node, index) => (
          <li key={index} className="mb-2">
            <a
              href={`#${node.id}`}
              onClick={(event) => handleLinkClick(event, node.id)}
              className="text-gray-700 hover:text-blue-600 shadow-md"
            >
              {node.text}
            </a>
            {node.children.length > 0 && renderTree(node.children, depth + 1)}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="blog-toc sticky top-0 overflow-y-auto max-h-screen p-4">
      <h2 className="text-lg font-bold mb-4">Table of Contents</h2>
      {renderTree(tree)}
    </div>
  );
};

export default TableOfContents;
