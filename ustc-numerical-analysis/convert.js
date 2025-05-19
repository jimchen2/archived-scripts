const fs = require("fs");
const path = require("path");
const md = require("markdown-it")();
const mk = require("@vscode/markdown-it-katex").default;

md.use(mk);

function getAllMarkdownFiles(dir) {
  let results = [];
  const items = fs.readdirSync(dir, { withFileTypes: true });

  for (const item of items) {
    if (item.name.startsWith(".")) continue;

    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) {
      results = results.concat(getAllMarkdownFiles(fullPath));
    } else if (path.extname(item.name).toLowerCase() === ".md") {
      results.push(fullPath);
    }
  }

  return results;
}

const mdFiles = getAllMarkdownFiles(".");

mdFiles.forEach((file) => {
  fs.readFile(file, "utf8", (err, data) => {
    const result = md.render(data);

    const htmlContent = `
          <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.0/dist/katex.min.css">
          ${result}

      `;

    const outputFile = file.replace(/\.md$/, ".html");
    const outputDir = path.dirname(outputFile);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Write the HTML content to the output file
    fs.writeFile(outputFile, htmlContent, (err) => {});
  });
});
