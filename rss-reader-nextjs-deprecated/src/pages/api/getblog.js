import db from "../../lib/db";

export default async function handler(req, res) {
  const id = parseInt(req.query.id);

  try {
    const { rows } = await db.query("SELECT * FROM rssblogs WHERE id = $1", [id]);

    if (rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: "Blog not found",
      });
    }

    res.status(200).json({
      success: true,
      blog: rows[0],
    });
  } catch (error) {
    console.error("Error fetching blog:", error);
    res.status(500).json();
  }
}