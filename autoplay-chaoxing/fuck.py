#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--disable-gpu")  # Applicable to windows os only
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
driver = webdriver.Chrome(options=chrome_options)


driver.get("https://passport2.chaoxing.com/mlogin")
wait = WebDriverWait(driver, 50)


# Find and fill the phone number field
phone_input = wait.until(EC.presence_of_element_located((
    By.ID, "phone"
)))
phone_input.send_keys("15026814735")

# Find and fill the password field
password_input = wait.until(EC.presence_of_element_located((
    By.ID, "pwd"
)))
password_input.send_keys("!")  # Replace with actual password

# Find and click the login button
login_button = wait.until(EC.element_to_be_clickable((
    By.CLASS_NAME, "btn-big-blue"
)))
login_button.click()
time.sleep(10) 


driver.get("https://ustc.fanya.chaoxing.com/courselist/course3")
link_xpath = "//a[contains(@href, '251143789')]"
link_element = wait.until(EC.presence_of_element_located((By.XPATH, link_xpath)))
course_url = link_element.get_attribute('href')
driver.get(course_url)



iframe = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "frame_content-zj"))
)
driver.switch_to.frame(iframe)


# Find the chapter element and click it
chapter_xpath = "//div[@id='cur968918905' and contains(@title, '正确处理改革开放前后两个30年的关系')]"
chapter_element = wait.until(EC.element_to_be_clickable((By.XPATH, chapter_xpath)))
chapter_element.click()

time.sleep(10)


driver.switch_to.default_content()
li_elements = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.posCatalog_select span.posCatalog_name"))
)

print(f"Found {len(li_elements)} elements to click")



for i, element in enumerate(reversed(li_elements)):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    title = element.get_attribute("title")    
    element.click()
    
    time.sleep(10)
    
    outer_iframe = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[info='card']"))
    )
    driver.switch_to.frame(outer_iframe)

    # Now that we're inside the first iframe, locate and switch to the inner iframe
    inner_iframe = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe.ans-attach-online.ans-insertvideo-online"))
    )
    driver.switch_to.frame(inner_iframe)
    
    play_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "vjs-big-play-button")))
    play_button.click()
    
    time.sleep(1200)
    driver.switch_to.parent_frame() 
    driver.switch_to.default_content()

