export default function Home() {
  const socialLinks = [
    { name: "GitHub", url: "https://github.com/jimchen2" },
    { name: "YouTube", url: "https://www.youtube.com/@JC-ss5nj" },
    { name: "WeChat", url: "/w.JPG" },
    { name: "QQ", url: "/qq.jpg" },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
      <div className="text-2xl font-bold">Hello, I am Jim Chen</div>
      <div>This is my blog. I write in English, Russian and Chinese.</div>
      <div className="text-2xl font-bold">All My Online Profiles</div>
      <ul>
        {socialLinks.map((link) => (
          <li key={link.name}>
            <a href={link.url}>
              - <span className="underline">{link.name}</span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
