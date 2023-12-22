#!/bin/bash

trap "echo -e '\nExiting...'; exit" SIGINT

while true; do
    content=""

    echo -n ">>> "
    # Read lines and check for the delimiter '\0'
    while IFS= read -r -e line; do
        if [[ "$line" == *'\0'* ]]; then
            # Remove the delimiter and append the rest to the content
            content+="${line%%\0*}"
            break
        fi
        content+="$line"
    done

    # Construct the JSON payload using jq
    json_payload=$(jq -n \
                      --arg content "$content" \
                      '{model: "gpt-4", messages: [{role: "user", content: $content}]}')
    
    clear      # Clear the screen
    echo "--------------------------"

    # Perform the API request
    response=$(curl -s https://api.openai.com/v1/chat/completions \
                  -H "Content-Type: application/json" \
                  -H "Authorization: Bearer $OPENAI_API_KEY" \
                  -d "$json_payload")

    # Check if the response contains an error
    if echo "$response" | jq -e '.error' > /dev/null; then
        errorMsg=$(echo "$response" | jq -r '.error.message')
        echo "Error: $errorMsg"
    else
        # Extract the content and display
        responseContent=$(echo "$response" | jq -r '.choices[0].message.content')
        echo -e "\n$responseContent\n"
    fi

    echo "--------------------------"

done
