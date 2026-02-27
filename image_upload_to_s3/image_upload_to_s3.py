import os
import re
import subprocess
import string
import random

CDN_URL = 'https://pub-0be4bc99725a45ac9b3be7ebcdc45895.r2.dev'
S3_REMOTE = 's3:cdn'

def upload_to_s3(local_file, s3_file):
    """Uploads a local file to the main S3 path."""
    target_path = f"{S3_REMOTE}/{s3_file}"
    try:
        subprocess.run(
            ["rclone", "copyto", local_file, target_path, "-P"],
            check=True,
            capture_output=True,
            text=True
        )        
        return f"{CDN_URL}/{s3_file}"
    except subprocess.CalledProcessError as e:
        print(f"  - ERROR uploading {local_file}: {e.stderr}")
        return None

def create_and_upload_thumbnail(local_file_path, s3_file_name):
    print(f"  + Creating thumbnail for {s3_file_name}...")
    thumbnail_s3_path = f"{S3_REMOTE}/thumbnail/{s3_file_name}"

    try:
        # Command now uses the modern 'magick convert' syntax to avoid deprecation warnings
        convert_command = [
            'magick', local_file_path,
            '-resize', '640x360^',
            '-gravity', 'center',
            '-crop', '640x360+0+0',
            '+repage',
            '-'
        ]
        
        convert_proc = subprocess.Popen(convert_command, stdout=subprocess.PIPE)
        
        rclone_proc = subprocess.run(
            ['rclone', 'rcat', thumbnail_s3_path],
            stdin=convert_proc.stdout,
            check=True,
            capture_output=True,
            text=True
        )
        
        convert_proc.stdout.close()
        
        print(f"  + Thumbnail uploaded: {thumbnail_s3_path}")

    except FileNotFoundError:
        print("  - ERROR: 'magick' command not found. Is ImageMagick installed and in your PATH?")
    except subprocess.CalledProcessError as e:
        print(f"  - ERROR creating thumbnail for {s3_file_name}: {e.stderr}")

def generate_short_id(length=6):
    characters = string.ascii_lowercase + string.digits
    return "".join(random.choices(characters, k=length))

def process_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    video_pattern = r'<video src="([^"]+\.mp4)" controls></video>'
    
    def replace_image(match):
        alt_text, image_url = match.groups()
        if CDN_URL not in image_url and not image_url.startswith(('http://', 'https://')):
            local_file = os.path.join(os.path.dirname(file_path), image_url)
            if os.path.exists(local_file):
                file_extension = os.path.splitext(local_file)[1]
                s3_file = f"{generate_short_id(6)}{file_extension}"
                
                print(f"  > Uploading image: {image_url} -> {s3_file}")
                new_url = upload_to_s3(local_file, s3_file)
                
                if new_url:
                    create_and_upload_thumbnail(local_file, s3_file)
                    return f'![{alt_text}]({new_url})'
        return match.group(0)

    def replace_video(match):
        video_url = match.group(1)
        if CDN_URL not in video_url and not video_url.startswith(('http://', 'https://')):
            local_file = os.path.join(os.path.dirname(file_path), video_url)
            if os.path.exists(local_file):
                file_extension = os.path.splitext(local_file)[1]
                s3_file = f"{generate_short_id(6)}{file_extension}"
                print(f"  > Uploading video: {video_url} -> {s3_file}")
                new_url = upload_to_s3(local_file, s3_file)
                if new_url:
                    return f'<video src="{new_url}" controls></video>'
        return match.group(0)
    
    new_content = re.sub(image_pattern, replace_image, content)
    new_content = re.sub(video_pattern, replace_video, new_content)
    
    if new_content != content:
        print(f"  * Rewriting {os.path.basename(file_path)} with updated links.")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)

def traverse_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                process_markdown_file(file_path)

def remove_local_media(directory):
    print("\nRemoving local media files...")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4')):
                file_path = os.path.join(root, file)
                print(f"  - Deleting {file_path}")
                os.remove(file_path)

target_dir = os.path.join('/home/user/Downloads/blog')

# Step 1: Upload Images and Videos to S3 and Replace in Markdown
traverse_directory(target_dir)

# Step 2: Remove local images and videos
remove_local_media(target_dir)
