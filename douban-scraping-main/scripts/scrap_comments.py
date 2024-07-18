from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient
import random

# Connect to MongoDB - Default is localhost:27017
client = MongoClient('mongodb://localhost:27017/')
db = client['douban']
discussions = db['discussions']
metadata = db['metadata']


# Generate 'links'
links = []
docs = discussions.find()
for doc in docs:
    if 'Link' in doc and 'Replies' in doc:
        replies = 0 if doc['Replies'] == '' else int(doc['Replies'])
        links.append(f"{doc['Link']}?start=0")
        if replies >= 100:
            pages = replies // 100
            for i in range(1, pages+1):
                links.append(f"{doc['Link']}?start={i * 100}")


               

def scrape_comment(url):
    # Set up Firefox options
    options = Options()
    options.add_argument("-headless") 
    options.preferences.update({"javascript.enabled": False})
    driver = webdriver.Firefox(options=options)

    try:
        # Navigate to the URL
        driver.get(url)

        # Wait for the topic replies to be loaded
        topic_replies = WebDriverWait(driver, 300).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "topic-reply"))
        )
        
        comments_data = []
        # Iterate through each reply-item within topic-reply
        for reply in topic_replies:
            comment_items = reply.find_elements(By.CLASS_NAME, "comment-item")
            for item in comment_items:
                comments_data.append(item.get_attribute('innerHTML'))  
        
    finally:
        # Close the browser window
        driver.quit()

    return comments_data


def extract_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the information
    douban_homepage = soup.find('a', href=True)['href']
    face_image_src = soup.find('img', class_='pil')['src']
    face_image_alt = soup.find('img', class_='pil')['alt']
    reply_content = soup.find('p', class_='reply-content').text.strip()
    reply_time = soup.find('span', class_='pubtime').text.strip()

    image_url = gif_url = None
    image_tag = soup.find('div', class_='cmt-img-wrapper')
    if image_tag:
        image_tag = image_tag.find('img')
    if image_tag:
        if image_tag.get('data-render-type') == 'gif':
            gif_url = image_tag.get('data-original-url')
            if gif_url.endswith('.jpg'):
                gif_url = gif_url[:-4] + '.mp4'
        else:
            image_url = image_tag.get('data-orig')

    # Initialize reply details and extract   
    reply_to_content = reply_to_author = None
    reply_section = soup.find('div', class_='reply-quote')
    if reply_section:
        reply_to_content = reply_section.find('span', class_='ref-content').text.strip()
        try:
            reply_to_author = reply_section.find('span', class_='pubdate').text.strip()
        except AttributeError:
            pass


    result = {
        "Douban Homepage": douban_homepage,
        "Face Image Source": face_image_src,
        "Face Image Alt": face_image_alt,
        "Reply Content": reply_content,
        "Reply Time": reply_time,
        "Image URL": image_url if image_url else "No media found",
        "GIF URL": gif_url if gif_url else "No media found",
        "Reply To Content": reply_to_content,
        "Reply To Author": reply_to_author
    }

    return result
    


uninserted_links = [link for link in links if not metadata.find_one({"link": link})]
print(uninserted_links)
random_links = random.sample(uninserted_links, min(20, len(uninserted_links)))

# # Loop over random links to scrape and store data
# for link in random_links:
#     if metadata.find_one({"link": link}):
#         print(f"Skipping link {link} as it's already processed.")
#         continue

#     comments_to_insert = []
#     link_parts = link.split('/')
#     subcollection_id = link_parts[-2]
#     start_value = int(link.split('=')[-1])
#     subcollection = db['comments'][subcollection_id]
#     comments_data = scrape_comment(link)

#     for i, html in enumerate(comments_data):
#         comment_index = str(start_value + i)
#         data = extract_data(html)
#         comments_to_insert.append({"_id": comment_index, "data": data})

#     if metadata.find_one({"link": link}):
#         print(f"Skipping link {link} as it's already processed.")
#         continue
        
#     if comments_to_insert:
#         subcollection.insert_many(comments_to_insert)
#         if not metadata.find_one({"link": link}):
#             metadata.insert_one({"link": link})
#             print(link)




# Loop over the specified links to scrape and store/update data
for link in random_links:
    subcollection_id = link.split('/topic/')[1].split('/')[0]
    subcollection = db['comments'][subcollection_id]
    comments_data = scrape_comment(link)
    comments_to_insert = []
    start_value = int(link.split('=')[-1])
    for i, html in enumerate(comments_data):
        comment_index = str(start_value + i)
        data = extract_data(html)
        comments_to_insert.append({"_id": comment_index, "data": data})
    for comment in comments_to_insert:
        subcollection.update_one({"_id": comment['_id']}, {"$set": comment}, upsert=True)
        print(comment['_id'],comment)
    print(f"Processed link: {link}")
