const fs = require("fs").promises;
const path = require("path");
const MarkdownIt = require("markdown-it");
const katexPlugin = require("@vscode/markdown-it-katex").default;

class Utils {
  static convertMarkdownToHtml(markdownContent) {
    const md = new MarkdownIt({
      html: true,
      breaks: true,
      linkify: true,
    });
    md.use(katexPlugin);

    return md.render(markdownContent);
  }
}

async function convertMarkdownFile(filePath) {
  try {
    const content = await fs.readFile(filePath, "utf-8");
    const htmlContent = Utils.convertMarkdownToHtml(content);
    const outputFile = path.join(path.dirname(filePath), path.basename(filePath, ".md") + ".html");

    const htmlOutput = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${path.basename(filePath, ".md")}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1, h2, h3 { color: #333; }
  </style>
</head>
<body>
  ${htmlContent}
</body>
</html>`;

    await fs.writeFile(outputFile, htmlOutput);
    console.log(`Successfully converted ${filePath} to ${outputFile}`);
  } catch (error) {}
}

async function main() {
  const filePath = process.argv[2];
  if (!filePath || !filePath.toLowerCase().endsWith(".md")) {
    console.error("Please provide a valid Markdown file path as an argument.");
    process.exit(1);
  }

  await convertMarkdownFile(filePath);
}

main();
