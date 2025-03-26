// src/pages/api/refreshall.js
import { Pool } from "pg";
import Parser from "rss-parser";

const pool = new Pool({
  connectionString: process.env.POSTGRES_URL,
});
const parser = new Parser();

export default async function handler(req, res) {
  try {
    const client = await pool.connect();

    // Get all subscriptions
    const subsResult = await client.query("SELECT * FROM subscriptions");
    const subscriptions = subsResult.rows;

    // Process each subscription
    for (const sub of subscriptions) {
      try {
        const feed = await parser.parseURL(sub.url);

        for (const item of feed.items) {
          await client.query(
            `
            INSERT INTO rssblogs (subscription_id, title, link, description, pub_date)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (link) DO UPDATE SET
              title = EXCLUDED.title,
              description = EXCLUDED.description,
              pub_date = EXCLUDED.pub_date
          `,
            [sub.id, item.title, item.link, item.contentSnippet || item.description, new Date(item.pubDate || item.isoDate)]
          );
        }
      } catch (feedError) {
        console.error(`Error processing feed ${sub.url}:`, feedError);
      }
    }

    client.release();
    res.status(200).json({ message: "Feeds refreshed successfully" });
  } catch (error) {
    console.error("Refresh error:", error);
    res.status(500).json({ message: "Internal server error" });
  }
}
