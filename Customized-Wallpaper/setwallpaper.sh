# Set the Wallpaper 

IMAGE_DIR="/home/username/Pictures/Wallpapers"
INDEX_FILE="$IMAGE_DIR/current_index.txt"

# If index file doesn't exist or index is greater than 20, initialize it with 1
if [ ! -f $INDEX_FILE  ]; then
    echo "1" > $INDEX_FILE
fi

# Read the current index for wallpaper setting
current_index=$(cat $INDEX_FILE)

# Gather all images and sort
sorted_images=($(ls "$IMAGE_DIR"/*.jpg | sort))

# If we have at least one image
if [ ${#sorted_images[@]} -gt 0 ]; then
    # Calculate modulus to cycle through available images
    image_index=$(( (current_index) % ${#sorted_images[@]} ))
    next_image="${sorted_images[$image_index]}"
    
    # Set the image as wallpaper using gsettings
    DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u username)/bus"
    gsettings set org.gnome.desktop.background picture-uri "file://$next_image"

    # Increment the index for next time
    current_index=$((current_index +1))
    echo $current_index > $INDEX_FILE
else
    echo "No images found in $IMAGE_DIR"
fi

