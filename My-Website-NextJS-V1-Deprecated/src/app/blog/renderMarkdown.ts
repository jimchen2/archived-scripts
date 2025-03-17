import { marked } from "marked";
import katex from "katex";

export const renderLatex = (markdown: string) => {
  const latexBlocks: { content: string; isInline: boolean }[] = [];
  let inCodeBlock = false;
  let codeBlockCount = 0;

  // Step 1: Extract LaTeX blocks and inline LaTeX, but not from code snippets
  let processedMarkdown = markdown
    .split("\n")
    .map((line) => {
      if (line.trim().startsWith("```")) {
        inCodeBlock = !inCodeBlock;
        codeBlockCount += inCodeBlock ? 1 : -1;
      }
      if (!inCodeBlock) {
        // Handle block LaTeX
        line = line.replace(/(\$\$.*?\$\$)/g, (match, latex) => {
          latexBlocks.push({ content: latex, isInline: false });
          return `<LATEX_${latexBlocks.length - 1}>`;
        });
        // Handle inline LaTeX
        line = line.replace(/(\$(?!\$).*?(?<!\$)\$)/g, (match, latex) => {
          latexBlocks.push({ content: latex, isInline: true });
          return `<LATEX_${latexBlocks.length - 1}>`;
        });
      }
      return line;
    })
    .join("\n");
  

  // Step 2: Render Markdown
  let renderedHtml = marked(processedMarkdown);

  // Step 3: Render LaTeX and replace placeholders
  for (let i = 0; i < latexBlocks.length; i++) {
    const { content, isInline } = latexBlocks[i];

    const latexContent = isInline ? content.slice(1, -1) : content.slice(2, -2);
    let renderedLatex;
    try {
      renderedLatex = katex.renderToString(latexContent, { displayMode: !isInline });
    } catch (error) {
      console.error(`Error rendering LaTeX: ${latexContent}`, error);
      renderedLatex = `<span style="color: red;">Error rendering LaTeX: ${latexContent}</span>`;
    }

    renderedHtml = renderedHtml.replace(`<LATEX_${i}>`, renderedLatex);
  }
  return renderedHtml;
};






// $ bob $

// $ "bob" $

// $$a_{1}^{2}+a_{2}$$

// $$ bob $$

// $$ bob 

// ## bob $$

// $ bob $$

// $$ bob $

// $ x + y = z $

// $ f(x) = \frac{1}{x^2} $

// $ \alpha \beta \gamma $

// $$ \int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2} $$

// $ \vec{F} = m\vec{a} $

// $ \sum_{i=1}^{n} i = \frac{n(n+1)}{2} $

// $$ \lim_{x \to 0} \frac{\sin x}{x} = 1 $$

// $ \mathbf{A} = \begin{pmatrix} a & b \\ c & d \end{pmatrix} $

// $ E = mc^2 $

// $$ \frac{d}{dx} \int_{a}^{x} f(t) dt = f(x) $$

// $ \text{P}(A|B) = \frac{\text{P}(B|A) \text{P}(A)}{\text{P}(B)} $

// $$ \nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t} $$

// $ \overline{x} = \frac{1}{n} \sum_{i=1}^{n} x_i $

// $$ \det \begin{vmatrix} a & b \\ c & d \end{vmatrix} = ad - bc $$

// $ \forall x \in \mathbb{R}, \exists y \in \mathbb{N} : y > x $