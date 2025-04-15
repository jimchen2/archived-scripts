import os
import re
import uuid
import subprocess

CDN_URL = 'https://cdn.jimchen.me'

def upload_to_s3(local_file, s3_file):
        target_path = f"s3:cdn/{s3_file}"
        subprocess.run(
            ["rclone", "copyto", local_file, target_path],
            capture_output=True,
            text=True
        )        
        return f"{CDN_URL}/{s3_file}"


def process_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image(match):
        alt_text, image_url = match.groups()
        
        if 'cdn.jimchen.me' not in image_url:
            local_file = os.path.join(os.path.dirname(file_path), image_url)
            
            if os.path.exists(local_file):
                file_extension = os.path.splitext(local_file)[1]
                s3_file = f"{uuid.uuid4()}{file_extension}"
                new_url = upload_to_s3(local_file, s3_file)
                if new_url:
                    return f'![{alt_text}]({new_url})'
        
        return match.group(0)
    new_content = re.sub(pattern, replace_image, content)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)

def traverse_directory(directory):
    for root, _ , files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                process_markdown_file(file_path)

target_dir = os.path.join('/home/user/Code/blog')

# Step 2: Upload Images to S3 and Replace Markdown
traverse_directory(target_dir)

# Step 3: Remove any Images locally
def remove_local_images(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(root, file)
                os.remove(file_path)
remove_local_images(target_dir)
