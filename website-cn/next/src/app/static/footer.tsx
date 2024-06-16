import React from "react";

const footerSections = [
  {
    title: "联系方式",
    links: [
      { href: "mailto:jimchen4214@gmail.com", text: "jimchen4214@gmail.com" },
      { href: "https://jimchen.me/w.JPG", text: "微信", external: true }
    ]
  },
  {
    title: "技术网站",
    links: [
      { href: "https://github.com/jimchen2", text: "GitHub", external: true },
      { href: "https://www.kaggle.com/jc4214", text: "Kaggle", external: true }
    ]
  },
  {
    title: "链接",
    links: [
      { href: "https://public.jimchen.me", text: "我的公共 S3 存储桶 (public.jimchen.me)", external: true },
      { href: "https://chat.jimchen.me", text: "我的 LLM 广场 1 (chat.jimchen.me)", external: true },
      { href: "https://lobe.jimchen.me/chat", text: "我的 LLM 广场 2 (lobe.jimchen.me/chat)", external: true } 

    ]
  }
];

const Footer = () => {
  return (
    <footer className="bg-gray-100 text-gray-800 py-8">
      <div className="container mx-auto px-4 md:px-8 lg:px-16">
        <div className="flex flex-wrap justify-between">
          {footerSections.map((section, index) => (
            <div key={index} className="w-full md:w-1/3 mb-4 md:mb-0">
              <h3 className="text-lg font-bold mb-2">{section.title}</h3>
              <ul className="text-sm">
                {section.links.map((link, linkIndex) => (
                  <li key={linkIndex}>
                    <a
                      href={link.href}
                      target={link.external ? "_blank" : undefined}
                      rel={link.external ? "noopener noreferrer" : undefined}
                      className="hover:text-gray-600"
                    >
                      {link.text}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-8 border-t border-gray-300 pt-4 flex justify-between items-center">
          <p className="text-sm text-gray-500">
            © 2024 cjm | 网页使用 Next.js 
          </p>
          <a
            href="https://github.com/jimchen2/website-cn"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-500 hover:text-gray-600"
          >
            源代码
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
