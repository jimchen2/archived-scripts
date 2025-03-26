// src/pages/api/addrss.js
import { Pool } from 'pg';
import axios from 'axios';
import Parser from 'rss-parser';

const pool = new Pool({
  connectionString: process.env.POSTGRES_URL
});

const rssParser = new Parser();

export default async function handler(req, res) {
  const { url } = req.query;

  if (!url) {
    return res.status(400).json({ message: 'URL is required' });
  }

  try {
    const client = await pool.connect();

    // Insert subscription and get the ID
    const subResult = await client.query(
      'INSERT INTO subscriptions (url) VALUES ($1) ON CONFLICT (url) DO UPDATE SET url = EXCLUDED.url RETURNING id',
      [url]
    );
    const subscriptionId = subResult.rows[0].id;

    // Fetch and parse RSS feed
    const response = await axios.get(url);
    const feed = await rssParser.parseString(response.data);

    // Extract header information
    const headerData = {
      title: feed.title || 'Untitled Feed',
      link: feed.link || url,
      description: feed.description || '',
      image_url: feed.image?.url || feed.itunes?.image || '' // Check common image locations
    };

    // Insert header data
    await client.query(
      `INSERT INTO header (subscription_id, title, link, description, image_url)
       VALUES ($1, $2, $3, $4, $5)`,
      [
        subscriptionId,
        headerData.title,
        headerData.link,
        headerData.description,
        headerData.image_url
      ]
    );

    client.release();
    res.status(200).json({ 
      message: 'Subscription and header added successfully',
      header: headerData
    });
  } catch (error) {
    console.error('Error adding subscription:', error);
    res.status(500).json({ 
      message: 'Internal server error',
      error: error.message 
    });
  }
}