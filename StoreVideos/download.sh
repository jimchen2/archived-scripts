#!/bin/bash

# Initialize variables and define usage function
VIDEO_URL="" WORKING_DIR="./videos/"
usage() { echo "Usage: $0 -v <video-url>"; exit 1; }

# Parse command line options
while getopts ":v:" opt; do
  case $opt in
    v) VIDEO_URL="$OPTARG" ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage ;;
    :) echo "Option -$OPTARG requires an argument." >&2; usage ;;
  esac
done
[ -z "$VIDEO_URL" ] && { echo "No video URL provided."; usage; }

# Prepare filenames
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
ORIGINAL_TITLE=$(yt-dlp --get-filename -o "%(title)s" "$VIDEO_URL" | tr -d '[:punct:]' | tr ' ' '_')
FILENAME_BASE="${WORKING_DIR}${ORIGINAL_TITLE}_${TIMESTAMP}"
SUBTITLED_FILENAME="${WORKING_DIR}${ORIGINAL_TITLE}_${TIMESTAMP}_subtitled.webm"

# Download video and subtitles
yt-dlp --write-auto-sub --sub-langs ru,en --skip-download "$VIDEO_URL" -o "${FILENAME_BASE}"
cat "${FILENAME_BASE}".{en,ru}.vtt > "${FILENAME_BASE}_combined.vtt"
yt-dlp "$VIDEO_URL" -o "${FILENAME_BASE}.webm"

# Apply subtitles using ffmpeg
ffmpeg -i "${FILENAME_BASE}.webm" -vf "subtitles=${FILENAME_BASE}_combined.vtt:force_style='BackColour=0x00000000,BorderStyle=4,Outline=1,Shadow=0'" -c:a copy "$SUBTITLED_FILENAME"

# Cleanup and return the path of the processed video
rm "${FILENAME_BASE}"{.webm,.en.vtt,.ru.vtt,_combined.vtt}
echo "Processing completed. Video saved to $SUBTITLED_FILENAME"
echo "$SUBTITLED_FILENAME"  # This line returns the path of the processed video
