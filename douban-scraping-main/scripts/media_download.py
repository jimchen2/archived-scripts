import os
import subprocess
from pymongo import MongoClient
from concurrent.futures import ProcessPoolExecutor

# Function to download a single file
def download_file(media):
    folder_name = '../media'  # Folder to save the downloaded files and the error log
    url = media['url']
    # Extract the filename from the URL
    filename = url.split('/')[-1]
    # Ensure filename is filesystem-friendly
    filename = filename.replace('/', '_').replace(':', '_')
    file_path = os.path.join(folder_name, filename)
    
    # Check if file already exists to avoid re-downloading
    if not os.path.exists(file_path):
        # Attempt to download and save the file using wget
        print(f"Downloading {url} using wget...")
        command = ['wget', '-O', file_path, url]
        try:
            subprocess.run(command, check=True)
            print(f"Saved {filename} successfully.")
        except subprocess.CalledProcessError:
            print(f"Error downloading {url}")
            # Log the error
            with open(os.path.join(folder_name, "download_errors.txt"), 'a') as error_log:
                error_log.write(f"{url}\n")

# Your MongoDB connection string
client = MongoClient('mongodb://localhost:27017/')

# Access the 'comment_media' database
media_db = client['comment_media']
# Access the collection within 'comment_media' database that stores URLs
media_collection = media_db['media_url']

# Folder to save the downloaded files and the error log
folder_name = '../media'
os.makedirs(folder_name, exist_ok=True)

# Fetch all documents in the media_urls collection
media_urls = list(media_collection.find({}))

# Use ProcessPoolExecutor to download files in parallel
with ProcessPoolExecutor(max_workers=500) as executor:
    executor.map(download_file, media_urls)

print("All files processed. Check download_errors.txt for any download failures.")

