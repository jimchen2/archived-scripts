#!/bin/bash

TELEGRAM_SCRIPT_PATH="/root/Downloads/uploadbilibili/downloadtelegram.py"
UPLOAD_SCRIPT_PATH="/root/Downloads/uploadbilibili/uploader.py"
DOWNLOAD_FOLDER="/root/Videos/"

pkill -f "$TELEGRAM_SCRIPT_PATH"
python3 "$TELEGRAM_SCRIPT_PATH" &

LAST_UPLOADED_VIDEO=""

while true; do
  NEWEST_VIDEO=$(find "$DOWNLOAD_FOLDER" -type f -name '*.mp4' -printf "%T@ %p\n" | sort -n | tail -1 | cut -f2- -d" ")
  if [[ "$NEWEST_VIDEO" != "$LAST_UPLOADED_VIDEO" ]]; then
    python3 "$UPLOAD_SCRIPT_PATH" --video_path "$NEWEST_VIDEO"
    LAST_UPLOADED_VIDEO="$NEWEST_VIDEO"
  fi
  sleep 30
done

