import { Link } from './types';

export const links: Link[] = [
  { name: "Blog", icon: "nextjs.png", url: "https://jimchen.me", category: "Apps" },
  { name: "Markdown Parser", icon: "nextjs.png", url: "https://markdown.jimchen.me", category: "Apps" },
  { name: "Git Server", icon: "gitea.png", url: "https://git.jimchen.me", category: "Apps" },
  { name: "Server Status", icon: "grafana.png", url: "https://grafana.jimchen.me/public-dashboards/b6c9b0826c0b4af6b7bd4324618c5b95", category: "Apps" },
  { name: "Mail", icon: "gmail.svg", url: "mailto:jimchen4214@gmail.com", category: "Social" },
  { name: "WeChat", icon: "wechat.svg", url: "./qr_code/wechat.jpeg", isQR: true, category: "Social" },
  { name: "QQ", icon: "tencentqq.svg", url: "./qr_code/qq.jpg", isQR: true, category: "Social" },
  { name: "RSS Feed", icon: "rss.svg", url: "https://jimchen.me/api/rss", category: "Social" },
  { name: "GitHub", icon: "github.svg", url: "https://github.com/jimchen2", category: "Tech" },
  { name: "Docker Hub", icon: "docker.svg", url: "https://hub.docker.com/u/jimchen2", category: "Tech" },
  { name: "Kaggle", icon: "kaggle.webp", url: "https://www.kaggle.com/jc4214", category: "Tech" },
  { name: "Hugging Face", icon: "huggingface.svg", url: "https://huggingface.co/jimchen2", category: "Tech" },
  { name: "Mastodon", icon: "mastodon.png", url: "https://mastodon.jimchen.me", category: "Fediverse" },
  { name: "PeerTube", icon: "peertube.png", url: "https://peertube.jimchen.me", category: "Fediverse" },
  { name: "Matrix", icon: "matrix.png", url: "https://app.element.io/#/user/@jc:matrix.jimchen.me", category: "Fediverse" },

];