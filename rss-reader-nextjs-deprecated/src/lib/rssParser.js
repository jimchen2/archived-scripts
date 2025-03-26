const Parser = require('rss-parser');
const parser = new Parser();

// RSS Parser Function
async function parseRSS(url) {
  try {
    const feed = await parser.parseURL(url);
    return feed.items.map(item => ({
      title: item.title || 'No title',
      link: item.link || '',
      description: item.contentSnippet || item.description || '',
      pubDate: new Date(item.pubDate || item.isoDate || Date.now()),
    }));
  } catch (error) {
    console.error(`Error parsing RSS feed ${url}:`, error);
    return [];
  }
}

module.exports = { parseRSS };