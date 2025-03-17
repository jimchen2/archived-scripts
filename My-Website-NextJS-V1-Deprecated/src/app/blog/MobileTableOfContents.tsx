import React from "react";

interface TOCProps {
  headings: { id: string; text: string; level: number }[];
}

interface TreeNode {
  id: string;
  text: string;
  level: number;
  children: TreeNode[];
}

const buildTree = (headings: TOCProps["headings"]): TreeNode[] => {
  const tree: TreeNode[] = [];
  const stack: TreeNode[] = [];

  for (const heading of headings) {
    const node: TreeNode = {
      id: heading.id,
      text: heading.text,
      level: heading.level,
      children: [],
    };

    while (stack.length > 0 && stack[stack.length - 1].level >= heading.level) {
      stack.pop();
    }

    if (stack.length === 0) {
      tree.push(node);
    } else {
      stack[stack.length - 1].children.push(node);
    }

    stack.push(node);
  }

  return tree;
};

const TableOfContents: React.FC<TOCProps> = ({ headings }) => {
  const tree = buildTree(headings);

  const handleLinkClick = (
    event: React.MouseEvent<HTMLAnchorElement, MouseEvent>,
    id: string
  ) => {
    event.preventDefault();
    const element = document.getElementById(id);
    if (element) {
      const offset = 70;
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
      <ul className={`space-y-2.5 ${depth > 0 ? 'ml-4' : ''}`}>
        {nodes.map((node, index) => (
          <li key={index} className={`text-md ${depth > 0 ? 'text-sm' : ''}`}>
            <a
              href={`#${node.id}`}
              onClick={(event) => handleLinkClick(event, node.id)}
              className="text-gray-600 hover:underline hover:text-gray-600 shadow-md"
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