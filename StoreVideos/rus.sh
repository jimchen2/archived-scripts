#!/bin/bash

# URL of the video
VIDEO_URL="https://invidious.asir.dev/watch?v=gZTBjjZlfS8"

# Generate a timestamp
TIMESTAMP=$(date +"%Y%m%d%H%M%S")

# Directory to save the video and subtitles
WORKING_DIR="./"

# Get the original video title (filename-safe) and append the timestamp
ORIGINAL_TITLE=$(yt-dlp --get-filename -o "%(title)s" "$VIDEO_URL" | tr -d '[:punct:]' | tr ' ' '_')
FILENAME_BASE="${WORKING_DIR}${ORIGINAL_TITLE}_${TIMESTAMP}"

# Download the video with Russian subtitles (but skip the video download itself)
yt-dlp --write-auto-sub --sub-langs ru --skip-download "$VIDEO_URL" -o "${FILENAME_BASE}"

# Download the video
yt-dlp "$VIDEO_URL" -o "${FILENAME_BASE}"

# Apply subtitles to the video using ffmpeg
ffmpeg -i "${FILENAME_BASE}.webm" -vf "subtitles=${FILENAME_BASE}.ru.vtt" -c:a copy "${WORKING_DIR}${ORIGINAL_TITLE}.webm"

# Remove the temporary video and subtitle files
rm "${FILENAME_BASE}.webm"
rm "${FILENAME_BASE}.ru.vtt"

echo "Processing completed. Files saved to ${WORKING_DIR}"
