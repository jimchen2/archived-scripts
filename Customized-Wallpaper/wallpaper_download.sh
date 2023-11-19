#!/bin/bash

PID=$(pgrep gnome-session -n)
export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS /proc/$PID/environ | tr '\0' '\n' | cut -d= -f2-)

# Variable Definitions
API_KEY="39432845-c4364b4ce06e456cbccafdf76"
SEARCH_TERMS=("iceland" "saint petersburg" "lofoten" "norway" "finland" "siberia" "switzerland")
USER_AGENT="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
IMAGE_DIR="/home/$USER/Pictures/Wallpapers"
MAX_IMAGES=20
INDEX_FILE="$IMAGE_DIR/current_index.txt"

# Count the current images in the directory
current_image_count=$(ls -1 "$IMAGE_DIR"/*.jpg 2>/dev/null | wc -l)

# If there are more than MAX_IMAGES, delete images until we reach MAX_IMAGES
while [ "$current_image_count" -gt "$MAX_IMAGES" ]; do
    oldest_image=$(ls "$IMAGE_DIR"/*.jpg | sort | head -n 1)
    echo "Deleting oldest image: $oldest_image"
    rm "$oldest_image"
    current_image_count=$(ls -1 "$IMAGE_DIR"/*.jpg 2>/dev/null | wc -l)
done

# Set the Wallpaper
if [ ! -f $INDEX_FILE ]; then
    echo "1" >$INDEX_FILE
fi
current_index=$(cat $INDEX_FILE)
sorted_images=($(ls "$IMAGE_DIR"/*.jpg | sort))
if [ ${#sorted_images[@]} -gt 0 ]; then
    image_index=$((current_index % ${#sorted_images[@]}))
    next_image="${sorted_images[$image_index]}"
    DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u $USER)/bus"

    # Set the image as wallpaper using gsettings and set it to 'zoomed' mode
    gsettings set org.gnome.desktop.background picture-uri "file://$next_image"
    gsettings set org.gnome.desktop.background picture-options 'zoom'

    current_index=$((current_index + 17))
    echo $current_index >$INDEX_FILE
else
    echo "No images found in $IMAGE_DIR"
fi

# Download the Wallpaper
mkdir -p "$IMAGE_DIR"
exec &>>"$IMAGE_DIR/wallpaper_downloader.log"

# Choose a random search term
SEARCH_TERM=${SEARCH_TERMS[$RANDOM % ${#SEARCH_TERMS[@]}]}
ENCODED_SEARCH_TERM=$(printf '%s' "$SEARCH_TERM" | sed 's/ /%20/g')

# Check for internet connectivity
wget -q --spider --user-agent="$USER_AGENT" https://google.com
if [[ $? -eq 0 ]]; then
    API_INFO_URL="https://pixabay.com/api/?key=$API_KEY&q=$ENCODED_SEARCH_TERM&image_type=photo"
    totalHits=$(curl -s "$API_INFO_URL" -H "User-Agent: $USER_AGENT" | jq '.totalHits')
    numPages=$((totalHits / 20 + 1))
    if [[ $totalHits -eq 0 ]]; then
        echo "No images found for $SEARCH_TERM."
        exit 1
    fi

    page_number=$((1 + RANDOM % numPages))
    API_URL="$API_INFO_URL&page=$page_number"
    image_urls=($(curl -s "$API_URL" -H "User-Agent: $USER_AGENT" | jq -r '.hits[].largeImageURL'))
    random_image_url=${image_urls[$RANDOM % ${#image_urls[@]}]}
    if [[ -z "$random_image_url" ]]; then
        echo "No image URL found."
    else
        new_file_name="$IMAGE_DIR/$(date +%s).jpg"
        wget "$random_image_url" -O "$new_file_name" --user-agent="$USER_AGENT"
        width=$(identify -format "%w" "$new_file_name")
        height=$(identify -format "%h" "$new_file_name")
        aspect_ratio=$(echo "$width/$height" | bc -l)

        # Adjusted the aspect ratio check to allow for a wider range of images
        if (($(echo "$aspect_ratio < 1.5" | bc -l))) || (($(echo "$aspect_ratio > 2.1" | bc -l))); then
            echo "Image aspect ratio is not within the accepted range. Deleting the image."
            rm "$new_file_name"
        else
            echo "Saved image to $new_file_name"
        fi
    fi
fi
