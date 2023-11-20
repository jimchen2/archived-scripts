#!/bin/bash

# Check if a markdown file name is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: tohtml <markdown_file>"
    exit 1
fi

# Define the markdown file and output HTML file
MARKDOWN_FILE=$1
HTML_FILE="${MARKDOWN_FILE%.md}.html"

# Pandoc command with the no-math.lua filter
pandoc --lua-filter=/usr/share/no-math.lua --no-highlight "$MARKDOWN_FILE" -o "$HTML_FILE"
