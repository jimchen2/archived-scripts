from pymongo import MongoClient

# Your MongoDB connection string
client = MongoClient('mongodb://localhost:27017/')

# Access your 'douban' database
db = client['douban']

# Get all collection names
all_collections = db.list_collection_names()
comment_collections = [col for col in all_collections if col.startswith('comments.')]

# The single search string
search_string = "鸡" 

# Iterate over each comment collection
for collection_name in comment_collections:
    collection = db[collection_name]
    
    # MongoDB query to find documents where 'Reply Content' contains the search string
    query = {'data.Reply Content': {'$regex': search_string, '$options': 'i'}}  # 'i' for case-insensitive
    
    matches = collection.find(query)
    
    # Iterate over matches and print them
    for match in matches:
        print(match)

