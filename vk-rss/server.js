const express = require("express");
const app = express();
const { getVKProfile } = require("./account.js");
const { getVKGroupInfo } = require("./group.js");
const { getVKPosts } = require("./get_posts.js");

const DEFAULT_VK_API_KEY = process.env.VK_API_KEY || "";

// RSS route for /account/:username?apiKey=...
app.get("/account/:username", async (req, res) => {
  const username = req.params.username;
  // Get API key from query parameter, fall back to default
  const apiKey = req.query.apiKey || DEFAULT_VK_API_KEY;
  const count = req.query.count || 15;

  // Check if API key is provided (either default or from user)
  if (!apiKey) {
    return res.status(400).send("API key is required. Please provide it using ?apiKey=YOUR_KEY");
  }

  try {
    // Fetch profile and posts concurrently
    const [profile, posts] = await Promise.all([getVKProfile(username, apiKey), getVKPosts(username, apiKey, count)]);

    // Generate RSS feed
    const rssFeed = generateRssFeed(profile, posts, username, req, apiKey);

    // Set content type and send RSS
    res.set("Content-Type", "application/rss+xml");
    res.send(rssFeed);
  } catch (error) {
    console.error("Error generating RSS:", error);
    res.status(500).send(`Error generating RSS feed: ${error.message}`);
  }
});

// RSS route for /group/:groupId?apiKey=...
app.get("/group/:groupId", async (req, res) => {
  const groupId = req.params.groupId;
  // Get API key from query parameter, fall back to default
  const apiKey = req.query.apiKey || DEFAULT_VK_API_KEY;
  const count = req.query.count || 15;

  // Check if API key is provided (either default or from user)
  if (!apiKey) {
    return res.status(400).send("API key is required. Please provide it using ?apiKey=YOUR_KEY");
  }

  try {
    // Fetch group info and posts concurrently
    const [groupInfo, posts] = await Promise.all([getVKGroupInfo(groupId, apiKey), getVKPosts(groupId, apiKey, count)]);

    // Generate RSS feed
    const rssFeed = generateRssFeed(groupInfo, posts, groupId, req, apiKey, true);

    // Set content type and send RSS
    res.set("Content-Type", "application/rss+xml");
    res.send(rssFeed);
  } catch (error) {
    console.error("Error generating RSS:", error);
    res.status(500).send(`Error generating RSS feed: ${error.message}`);
  }
});

// Function to generate RSS feed for both accounts and groups
function generateRssFeed(profile, posts, username, req, apiKey, isGroup = false) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>${profile.name}'s VK Feed</title>
        <link>https://vk.com/${username}</link>
        <description>${escapeXml(profile.description)}</description>
        <image>
            <url>${escapeXml(profile.imageUrl)}</url>
            <title>${profile.name}'s ${isGroup ? "Group" : "Profile"} Picture</title>
            <link>https://vk.com/${username}</link>
        </image>
        <atom:link href="http://${req.headers.host}/${isGroup ? "group" : "account"}/${username}?apiKey=${encodeURIComponent(apiKey)}" rel="self" type="application/rss+xml" />
        ${posts
          .map(
            (post) => `
        <item>
            <title>${escapeXml(post.title)}</title>
            <link>${post.link}</link>
            <guid>${post.link}</guid>
            <pubDate>${new Date(post.date).toUTCString()}</pubDate>
            <description><![CDATA[${post.articleHtml}]]></description>
        </item>`
          )
          .join("\n")}
    </channel>
</rss>`;
}

// Function to escape XML special characters
function escapeXml(unsafe) {
  if (!unsafe) return "";
  return unsafe.replace(/[<>&'"]/g, (c) => {
    switch (c) {
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case "&":
        return "&amp;";
      case "'":
        return "&apos;";
      case '"':
        return "&quot;";
      default:
        return c;
    }
  });
}

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
