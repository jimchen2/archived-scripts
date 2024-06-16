import boto3
import re
from datetime import datetime

# User Configuration
bucket_name = 'blog'  # Replace with your S3 bucket name
input_markdown_file = 'review.md'  # Replace with your input markdown file
output_markdown_file_prefix = 'review_updated'  # Prefix for the output markdown file

# AWS Credentials
aws_access_key_id = 'your-access-key-id'
aws_secret_access_key = 'your-secret-access-key'
endpoint_url = 'https://s3.amazonaws.com'  # Default S3 endpoint URL

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    endpoint_url=endpoint_url
)

def upload_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        s3.upload_file(file_name, bucket, object_name)
        print(f"Upload Successful: {file_name} to {object_name}")
        return f"https://{bucket}.s3.amazonaws.com/{object_name}"
    except Exception as e:
        print(f"Upload Failed: {e}")
        return None

def replace_image_paths(content, bucket):
    image_paths = re.findall(r'!\[.*?\]\((.*?)\)', content)
    s3_urls = {}
    
    for image_path in image_paths:
        s3_url = upload_to_s3(image_path, bucket)
        if s3_url:
            s3_urls[image_path] = s3_url
    
    for local_path, s3_url in s3_urls.items():
        content = content.replace(local_path, s3_url)
    
    return content

def main():
    # Read the markdown file
    with open(input_markdown_file, 'r') as file:
        content = file.read()

    # Replace local image paths with S3 URLs
    updated_content = replace_image_paths(content, bucket_name)

    # Save the updated content to a new markdown file
    new_file_name = f'{output_markdown_file_prefix}_{datetime.now().strftime("%Y%m%d%H%M%S")}.md'
    with open(new_file_name, 'w') as file:
        file.write(updated_content)

    print(f"Updated markdown file saved as {new_file_name}")

if __name__ == "__main__":
    main()

