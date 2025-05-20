import os
import requests
import subprocess
import tempfile
from datetime import datetime
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_repo_urls(token):
    logger.info("Fetching repository URLs...")
    headers = {'Authorization': f'Bearer {token}'}
    all_repo_urls = []
    page = 1

    while True:
        response = requests.get(f'https://api.github.com/user/repos?page={page}&per_page=100', headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch repos: {response.status_code} - {response.text}")
            sys.exit(1)
            
        repos = response.json()
        if not repos:
            break
        
        all_repo_urls.extend(repo['clone_url'] for repo in repos)
        logger.info(f"Found {len(repos)} repositories on page {page}")
        page += 1
    
    logger.info(f"Total repositories found: {len(all_repo_urls)}")
    return all_repo_urls

def clone_all_repos(token, repos, base_dir):
    logger.info(f"Cloning {len(repos)} repositories to {base_dir}...")
    
    for repo_url in repos:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        auth_url = repo_url.replace("https://", f"https://oauth2:{token}@")
        
        logger.info(f"Cloning {repo_name}...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", auth_url],
            cwd=base_dir,
            capture_output=True,
            text=True
        )

def setup_rclone(rclone_config):
    logger.info("Setting up rclone...")
    os.makedirs(os.path.dirname(rclone_config), exist_ok=True)
    rclone_conf_content = os.environ.get('RCLONE_CONFIG_CONTENT')
    if not rclone_conf_content:
        logger.error("RCLONE_CONFIG_CONTENT environment variable not set")
        sys.exit(1)
        
    with open(rclone_config, 'w') as f:
        f.write(rclone_conf_content)
        
    logger.info("rclone configuration set up successfully")

def create_backup_archive(source_dir):
    # Format date as YYYYMMDD and time as HHMM
    current_date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%H%M")
    
    archive_name = f"github_backup_{current_date}_{current_time}.tar.gz"
    archive_path = os.path.join(tempfile.gettempdir(), archive_name)
    
    result = subprocess.run(
        ["tar", "-czf", archive_path, "-C", os.path.dirname(source_dir), os.path.basename(source_dir)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to create archive: {result.stderr}")
        sys.exit(1)
    
    logger.info(f"Archive created at {archive_path}")
    return archive_path

def upload_to_gdrive(archive_path, rclone_config):
    gdrive_path = "google:github-backup/"
    
    logger.info(f"Uploading {archive_path} to {gdrive_path}...")
    result = subprocess.run(
        ["rclone", "--config", rclone_config, "copy", archive_path, gdrive_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to upload to Google Drive: {result.stderr}")
        sys.exit(1)
        
    logger.info(f"Successfully uploaded to Google Drive")

def main():
    logger.info("Starting GitHub backup process...")
    
    github_token = os.environ.get('TOKEN')

    # Setup temporary directories
    temp_dir = tempfile.mkdtemp()
    git_folder = os.path.join(temp_dir, "git_backup")
    os.makedirs(git_folder, exist_ok=True)
    rclone_config = os.path.expanduser("~/.config/rclone/rclone.conf")
    
    repos = get_repo_urls(github_token)
    clone_all_repos(github_token, repos, git_folder)
    setup_rclone(rclone_config)
    archive_path = create_backup_archive(git_folder)
    upload_to_gdrive(archive_path, rclone_config)

if __name__ == "__main__":
    main()
