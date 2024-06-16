#!/bin/bash

# Function to download images
download_images() {
  local file=$1
  local folder=$2
  mkdir -p "$folder"

  grep -oP '!\[.*?\]\(\K(https?://[^\)]*)' "$file" | while read -r url; do
    wget -P "$folder" "$url"
  done
}

# Function to convert markdown to PDF
convert_to_pdf() {
  local file=$1
  local folder=$2
  local title=$(grep -m 1 '^title: ' "$file" | sed 's/^title: "\(.*\)"$/\1/')
  local pdf_file="${folder}/${title}.pdf"

  pandoc "$file" --resource-path="$folder" --pdf-engine=xelatex \
    -V mainfont="Noto Serif" -V monofont="Noto Sans Mono" -V sansfont="Noto Sans" \
    -o "$pdf_file"
}

# Main process
main() {
  for file in *.md; do
    # Extract type from the markdown file
    local type=$(grep -m 1 '^type: ' "$file" | sed 's/^type: \(.*\)$/\1/')
    
    # Create a folder based on the type
    type_folder="${type}"
    mkdir -p "$type_folder"
    
    # Create a folder for images
    image_folder="${type_folder}/images"
    
    # Download images
    download_images "$file" "$image_folder"
    
    # Convert to PDF
    convert_to_pdf "$file" "$type_folder"
  done
}

# Run the main process
main
