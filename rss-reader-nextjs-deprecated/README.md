## `vercel.json`

Cronjob to refetch RSS blogs.

## Create Types in Postgres

```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    url VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE header (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES subscriptions(id),
    title VARCHAR(255),
    link VARCHAR(255),
    description TEXT,
    image_url VARCHAR(255)
);

CREATE TABLE rssblogs (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES subscriptions(id),
    title VARCHAR(255),
    link VARCHAR(255) UNIQUE,
    description TEXT,
    pub_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Routes

- `/api/getblogsmetadata?offset=&limit=`: Get metadata for blogs with date in reverse order. For example, fetching the 10th to 20th latest blogs would be offset=10 and limit=10.
- `/api/getblog?id=`: Get a single blog
- `/api/addrss?url=`: Add a subscription and the header
- `/api/refreshall`: Fetch/Refresh all feeds
