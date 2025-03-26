import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.POSTGRES_URL,
});

export default async function handler(req, res) {
  const { offset = 0, limit = 10 } = req.query;

  try {
    const client = await pool.connect();
    const result = await client.query(
      `
      SELECT 
        r.*,
        h.title AS header_title,
        h.link AS header_link,
        h.image_url AS header_image_url
      FROM rssblogs r
      LEFT JOIN header h ON r.subscription_id = h.subscription_id
      ORDER BY r.pub_date DESC
      OFFSET $1 LIMIT $2
    `,
      [parseInt(offset), parseInt(limit)]
    );

    client.release();
    res.status(200).json(result.rows);
  } catch (error) {
    console.error("Error fetching blogs metadata:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}