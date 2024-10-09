import json
import os
import subprocess
import boto3
from urllib.request import urlretrieve
import urllib.parse

s3_client = boto3.client('s3')

def install_ffmpeg():
    print("Installing ffmpeg and ffprobe...")
    ffmpeg_url = "https://public.jimchen.me/ffmpeg/ffmpeg-bin"
    ffprobe_url = "https://public.jimchen.me/ffmpeg/ffprobe"
    
    # Download FFmpeg
    urlretrieve(ffmpeg_url, "/tmp/ffmpeg")
    
    # Download FFprobe
    urlretrieve(ffprobe_url, "/tmp/ffprobe")
    
    # Make them executable
    os.chmod("/tmp/ffmpeg", 0o755)
    os.chmod("/tmp/ffprobe", 0o755)
    
    print("ffmpeg and ffprobe installed")

def check_password(event):
    password = event.get('password')
    if not password or password != os.environ['FUNCTION_PASSWORD']:
        raise Exception('Invalid password')

def download_file(url, local_filename):
    encoded_url = urllib.parse.quote(url, safe=':/?&=')
    urlretrieve(encoded_url, local_filename)

def extract_frame(input_file, output_file, timestamp):
    subprocess.call(['/tmp/ffmpeg', '-i', input_file, '-ss', timestamp, '-vframes', '1', output_file])

def create_previewVideo(input_file, output_file, start_time, duration):
    subprocess.call(['/tmp/ffmpeg', '-i', input_file, '-ss', start_time, '-t', duration, '-vf', 'scale=320:-1', output_file])

def upload_to_s3(local_file, bucket, s3_key):
    s3_client.upload_file(local_file, bucket, s3_key)
    return f"https://{bucket}.s3.amazonaws.com/{s3_key}"

def time_to_seconds(time_str):
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

def lambda_handler(event, context):
    try:
        # Install ffmpeg and ffprobe
        install_ffmpeg()

        # Check password
        check_password(event)

        url = event['url']
        s3_object_key = event['s3ObjectKey']
        preview_image_timestamp = event['previewImageTimestamp']
        previewVideo_start = event['previewVideoStart']
        previewVideo_end = event['previewVideoEnd']
        bucket = event['bucket']

        # Download video
        local_video = '/tmp/video.mp4'
        download_file(url, local_video)

        # Extract preview image
        preview_image = '/tmp/preview.jpg'
        extract_frame(local_video, preview_image, preview_image_timestamp)

        # Create previewVideo
        previewVideo = '/tmp/previewVideo.gif'
        previewVideo_duration = str(time_to_seconds(previewVideo_end) - time_to_seconds(previewVideo_start))
        create_previewVideo(local_video, previewVideo, previewVideo_start, previewVideo_duration)

        # Upload to S3 and get URLs
        preview_image_key = f"{s3_object_key}_preview.jpg"
        previewVideo_key = f"{s3_object_key}_previewVideo.gif"

        preview_image_url = upload_to_s3(preview_image, bucket, preview_image_key)
        previewVideo_url = upload_to_s3(previewVideo, bucket, previewVideo_key)

        # Clean up local files
        os.remove(local_video)
        os.remove(preview_image)
        os.remove(previewVideo)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'previewImageUrl': preview_image_url,
                'previewVideoUrl': previewVideo_url
            })
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)})
        }