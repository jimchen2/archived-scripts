#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize the embedding model (multilingual)
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="user",
)
cur = conn.cursor()

# Read documents
documents = [
    {
        "title": "Russia Wikipedia",
        "file": "doc1",
        "language": "Russian"
    },
    {
        "title": "USA Wikipedia", 
        "file": "doc2",
        "language": "English"
    },
    {
        "title": "Three Gorges Dam Wikipedia",
        "file": "doc3",
        "language": "English"
    },
    {
        "title": "Yosemite National Park Wikipedia",
        "file": "doc4",
        "language": "English"
    }
]

# Process each document
for doc in documents:
    try:
        with open(doc["file"], 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Generate embedding
        embedding = model.encode(content)
        
        # Insert or update if exists (based on title)
        cur.execute("""
            INSERT INTO documents (title, content, language, embedding)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (title) 
            DO UPDATE SET
                content = EXCLUDED.content,
                language = EXCLUDED.language,
                embedding = EXCLUDED.embedding
        """, (doc["title"], content, doc["language"], embedding.tolist()))
        
        print(f"Upserted: {doc['title']}")
    except Exception as e:
        print(f"Error with {doc['file']}: {e}")

conn.commit()
cur.close()
conn.close()