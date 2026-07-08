const Redis = require('ioredis');

const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

const redis = new Redis(redisUrl);
const redisSubscriber = new Redis(redisUrl);

module.exports = {
  redis,
  redisSubscriber
};
