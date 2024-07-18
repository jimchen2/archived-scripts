from bs4 import BeautifulSoup
from pymongo import MongoClient

# Your MongoDB connection string
client = MongoClient('mongodb://localhost:27017/')

# Access your 'douban' database
db = client['douban']

# Access or create a new 'media_db' database and a new collection within 'media_db' for storing URLs
media_db = client['topic_media']
media_collection = media_db['media_url']

# Ensure the 'url' field is unique within the collection
media_collection.create_index("url", unique=True)

# Specify the name of the collection you want to process
collection = db['topics'] 

# Iterate over all documents in the collection
documents = collection.find({})  # Empty query to select all documents

# Iterate over documents to extract image URLs with BeautifulSoup
for doc in documents:
    if 'Main Content' in doc:
        html_content = doc['Main Content']
        soup = BeautifulSoup(html_content, 'html.parser')
        images = soup.find_all('img')
        img_sources = [img['src'] for img in images if 'src' in img.attrs]
        # Check each 'src' URL if it exists and is not "No media found", and if it's a duplicate
        for src in img_sources:
            if src and src != "No media found":
                if media_collection.count_documents({'url': src}) == 0:
                    media_collection.insert_one({'url': src})

print("Extraction and insertion of URLs completed.")

