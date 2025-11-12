#!/usr/bin/env python3
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from pgvector.psycopg2 import register_vector

def search_interactive():
    """
    An interactive command-line tool to perform semantic search on the documents
    stored in the PostgreSQL database.
    """
    print("Loading the sentence transformer model... (This may take a moment)")
    try:
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        print("✅ Model loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    conn = None
    try:
        print("Connecting to the database...")
        conn = psycopg2.connect(
            dbname="user",
        )
        cur = conn.cursor()
        register_vector(conn)
        print("✅ Database connection successful and vector type registered.")

        while True:
            query = input("\nEnter your search query (or type 'quit' to exit): ")

            if query.lower() in ['quit', 'exit']:
                break
            
            if not query.strip():
                continue

            print("   Generating embedding for your query...")
            query_embedding = model.encode(query)
            
            # ### CHANGE HERE ###
            # Temporarily disable the index to force an "exact" search.
            # This guarantees all documents are checked, which is fine for a small dataset.
            cur.execute("SET LOCAL enable_indexscan = off;")

            cur.execute(
                """
                SELECT id, title, language, (embedding <=> %s) AS distance
                FROM documents
                ORDER BY distance
                """,
                (query_embedding,)
            )

            results = cur.fetchall()

            print("\n--- Top Search Results ---")
            if not results:
                print("No matches found.")
            else:
                for row in results:
                    doc_id, title, language, distance = row
                    similarity = 1 - distance
                    
                    print(f"\n  📄 Title: {title}")
                    print(f"     Language: {language}")
                    # A negative similarity just means the vectors are pointing in opposite directions.
                    # This is common for unrelated queries.
                    print(f"     Similarity: {similarity:.4f} (Distance: {distance:.4f})")

            print("\n" + "="*50)

    except psycopg2.OperationalError as e:
        print(f"\n❌ Database connection failed: {e}")
        print("   Please ensure PostgreSQL is running and the 'user' database exists.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("\nConnection closed. Goodbye!")

if __name__ == "__main__":
    search_interactive()