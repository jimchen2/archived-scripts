#!/bin/bash

# Path to the video
VIDEO_URL="https://yewtu.be/watch?v=EX5hcbzZCow"

# Call download.sh with the video URL and capture the output
DOWNLOADED_VIDEO_PATH=$(./download.sh -v "$VIDEO_URL")

# Print the path of the downloaded video
echo "Downloaded video path: $DOWNLOADED_VIDEO_PATH"

