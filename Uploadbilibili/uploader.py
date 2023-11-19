import argparse
import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys

def parse_args():
    parser = argparse.ArgumentParser(description="Upload a video.")
    default_path = os.path.expanduser('~/Downloads/334406637_821984086235084_4311433350757638880_n.mp4')
    parser.add_argument('-path', '--video_path', default=default_path, help='Path to the video file')
    return parser.parse_args()

def setup_driver():
    profile_path = os.path.expanduser('~/.mozilla/firefox/4sspe6o3.default-release')
    options = FirefoxOptions()
    options.profile = profile_path
    service = FirefoxService(executable_path="/usr/local/bin/geckodriver")
    return webdriver.Firefox(service=service, options=options)

def upload_video(driver, video_path, tags):
    driver.get("https://member.bilibili.com/platform/upload/video/frame")
    WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".upload-btn")))
    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    file_input.send_keys(video_path)

    time.sleep(30)
    tag_input = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='按回车键Enter创建标签']")))
    for tag in tags:
        tag_input.send_keys(tag + Keys.ENTER)

    time.sleep(30)
    WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".submit-add"))).click()
    print("Video submitted.")

def main():
    args = parse_args()
    driver = setup_driver()
    upload_video(driver, args.video_path, ["valieva"])
    time.sleep(500)
    driver.quit()

if __name__ == "__main__":
    main()
