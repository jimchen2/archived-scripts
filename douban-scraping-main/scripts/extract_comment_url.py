from pymongo import MongoClient

# Your MongoDB connection string
client = MongoClient('mongodb://localhost:27017/')

# Access your 'douban' database
db = client['douban']

# Access the 'comment_media' database
media_db = client['comment_media']
# Define or access a collection within 'comment_media' database for storing URLs
media_collection = media_db['media_urls']

# Ensure the 'url' field is unique within the collection
media_collection.create_index("url", unique=True)

# Get all collection names from 'douban' database that contain comments
comment_collections = [col for col in db.list_collection_names() if col.startswith('comments.')]

# Iterate over each comment collection
for collection_name in comment_collections:
    collection = db[collection_name]
    
    # Iterate over all documents in the collection
    matches = collection.find({})  # Empty query to select all documents
    
    # Iterate over matches to extract URLs
    for match in matches:
        image_url = match['data'].get('Image URL')
        gif_url = match['data'].get('GIF URL')
        
        # Check 'Image URL' if it exists and is not "No media found"
        if image_url and image_url != "No media found":
            # Check if the URL already exists in the media_collection
            if media_collection.count_documents({'url': image_url}) == 0:
                # Insert the URL if it's not a duplicate
                media_collection.insert_one({'type': 'image', 'url': image_url})
        
        # Check 'GIF URL' if it exists and is not "No media found"
        if gif_url and gif_url != "No media found":
            # Check if the URL already exists in the media_collection
            if media_collection.count_documents({'url': gif_url}) == 0:
                # Insert the URL if it's not a duplicate
                media_collection.insert_one({'type': 'gif', 'url': gif_url})

print("Extraction and insertion of URLs completed.")

