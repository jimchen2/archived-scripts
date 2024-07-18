from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from bs4 import BeautifulSoup
import re


def scrape_discussion_list_html(url):
    # Set up Firefox options
    options = Options()
    options.preferences.update({"javascript.enabled": True})
    driver = webdriver.Firefox(options=options)
    
    html_content = ''
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Wait for the discussions table to be loaded
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.olt"))
        )
        
        # Get the outer HTML of the discussions table
        discussions_table = driver.find_element(By.CSS_SELECTOR, "table.olt")
        html_content = discussions_table.get_attribute('outerHTML')
        
    finally:
        # Close the browser window
        driver.quit()
    
    return html_content
    
def parse_discussions(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    discussions = []
    
    # Use a regular expression to match the numerical topic ID in the URL
    topic_id_pattern = re.compile(r'/topic/(\d+)/')
    
    # Find all discussion rows in the table
    rows = soup.find_all('tr')
    for row in rows:
        try:
            title_cell = row.find('td', class_='title')
            title = title_cell.find('a').get_text(strip=True)
            link = title_cell.find('a')['href']
            
            # Extract the topic ID from the URL using the regular expression
            topic_id_match = topic_id_pattern.search(link)
            topic_id = topic_id_match.group(1) if topic_id_match else 'Unknown'
            
            author = row.find('td', nowrap='nowrap').find('a').get_text(strip=True)
            
            replies = row.find('td', class_='r-count').get_text(strip=True)
            
            last_post_time = row.find('td', class_='time').get_text(strip=True)
            
            discussions.append({
                'Title': title,
                'Link': link,
                'Topic ID': topic_id,  # Include the extracted topic ID
                'Author': author,
                'Replies': replies,
                'Last Post Time': last_post_time
            })
        except AttributeError:
            # Skip rows that do not have the expected structure
            continue
    
    return discussions

# Pseudo-code representation
discussion_metadata = []

# Loop through the specified page offsets
for start in range(0, 175, 25):
    # url = f"https://www.douban.com/group/[]/discussion?start={start}"
    
    html_content = scrape_discussion_list_html(url)
    
    page_discussions = parse_discussions(html_content)
    
    discussion_metadata.extend(page_discussions)
    print(page_discussions)
    print(len(page_discussions))

print(discussion_metadata)
print(len(discussion_metadata))



from pymongo import MongoClient

# Connect to the MongoDB database server
client = MongoClient('mongodb://localhost:27017/')

db = client['douban']  # 'douban' is the database name
collection = db['discussions']  # 'discussions' is the collection name

# Initialize a dictionary to hold documents that don't exist in the collection
documents_to_insert = {}

# Check each document to see if it already exists in the collection
for document in discussion_metadata:
    result = collection.update_one(
        {'Link': document['Link']},  # Query condition for matching documents
        {'$set': document},          # Update or insert the document
        upsert=True                  # Insert a new document if none match the query condition
    )
    
    # Check the result and print appropriate messages
    if result.matched_count > 0:
        print(f"Updated document with Link: {document['Link']}")
    elif result.upserted_id:
        print(f"Inserted new document with ID: {result.upserted_id}")
    else:
        print(f"No changes made for Link: {document['Link']}")
