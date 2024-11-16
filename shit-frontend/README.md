```
sudo -u postgres createdb jimchen_blog
```

ToDo: RSS, Search

## Database

```
model Post {
  id           String   @id @default(uuid()) @db.Uuid
  title        String   @db.Text
  text         String   @db.Text
  lang         String   @db.VarChar(2)
  type         String   @db.VarChar(50)
  publishedAt  DateTime @db.Timestamp()
  search_vector 
  
  @@map("posts")
  @@unique([title, lang, type])
}

```

## Search

```
-- Add search vector column
ALTER TABLE posts ADD COLUMN search_vector tsvector
GENERATED ALWAYS AS (
  CASE
    WHEN lang = 'en' THEN
      setweight(to_tsvector('english', coalesce(title,'')), 'A') ||
      setweight(to_tsvector('english', coalesce(text,'')), 'B')
    WHEN lang = 'zh' THEN
      setweight(to_tsvector('simple', coalesce(title,'')), 'A') ||
      setweight(to_tsvector('simple', coalesce(text,'')), 'B')
    WHEN lang = 'ru' THEN
      setweight(to_tsvector('russian', coalesce(title,'')), 'A') ||
      setweight(to_tsvector('russian', coalesce(text,'')), 'B')
  END
) STORED;

-- Create the search index
CREATE INDEX posts_search_idx ON posts USING GIN (search_vector);
```
