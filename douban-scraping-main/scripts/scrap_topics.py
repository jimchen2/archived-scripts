
from pymongo import MongoClient

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from bs4 import BeautifulSoup
import re




client = MongoClient('mongodb://localhost:27017/')
db = client['douban']
collection = db['discussions']
docs = collection.find()
links = [doc['Link'] for doc in docs if 'Link' in doc]


def scrape_topic_content(url):

    options = Options()
    options.preferences.update({"javascript.enabled": True}) 
    options.add_argument("-headless") 
    driver = webdriver.Firefox(options=options)

    topic_content_html = ''
    try:
        driver.get(url)
        topic_content = WebDriverWait(driver, 100).until(
            EC.presence_of_element_located((By.CLASS_NAME, "topic-content"))
        )
        topic_content_html = topic_content.get_attribute('outerHTML')
        
    finally:
        # Close the browser window
        driver.quit()

    return topic_content_html
    
def extract_topic_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the user information
    user_link = soup.find('a', href=True)
    user_href = user_link['href'] if user_link else 'No link found'
    user_img_src = soup.find('img', class_='pil')['src'] if soup.find('img', class_='pil') else 'No image found'
    user_img_alt = soup.find('img', class_='pil')['alt'] if soup.find('img', class_='pil') else 'No alt text found'

    # Extract the post time
    post_time = soup.find('span', class_='create-time').text if soup.find('span', class_='create-time') else 'No time found'

    # Extract the main content text
    main_content_div = soup.find('div', class_='rich-content')
    
    # Return the entire HTML content of the main topic as a string
    main_content_html = str(main_content_div) if main_content_div else 'No content found'

    result = {
        "User Profile URL": user_href,
        "User Image Source": user_img_src,
        "User Image Alt Text": user_img_alt,
        "Post Time": post_time,
        "Main Content": main_content_html,
    }

    return result
    

client = MongoClient('mongodb://localhost:27017/')
db = client['douban']  # 'douban' is the database name
collection = db['topics']  # 'topics' is the collection name

def process_url(url):
    if is_already_inserted(url):
        print(f"URL '{url}' is already inserted. Skipping.")
        return

    try:
        topic_data = scrape_topic_content(url)
        topic_data_extracted = extract_topic_content(topic_data)
        topic_data_extracted["Link"] = url
        if is_already_inserted(url):
            return
        collection.insert_one(topic_data_extracted)
        print("Inserted topic:", topic_data_extracted)
    except Exception as e:
        print(f"Error processing URL '{url}': {e}")

        
        
        
        
        
        
def is_already_inserted(url):
    result = collection.find_one({"Link": url})
    return False if result is None else True
    
    
import random

def get_five_uninserted_urls(links):
    uninserted_urls = [url for url in links if not is_already_inserted(url)]
    return random.sample(uninserted_urls, 5) if len(uninserted_urls) >= 5 else uninserted_urls
    
selected_links = get_five_uninserted_urls(links)

for url in selected_links:
    process_url(url)




