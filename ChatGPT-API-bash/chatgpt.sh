#!/bin/bash

trap "echo -e '\nExiting...'; exit" SIGINT

while true; do
    content=""
    echo "Type your content. Press 'Enter' twice to finish input."
    
    # Read lines until an empty line (double Enter) is encountered
    while IFS= read -r -e line; do
        if [ -z "$line" ]; then
            break
        fi
        content+="$line\n"
    done

    # Echo a message indicating the request is being sent
    echo "Fetching response..."

    # Construct the JSON payload using jq
    json_payload=$(jq -n \
                      --arg content "$content" \
                      '{model: "gpt-4", messages: [{role: "user", content: $content}]}')

    # Perform the API request
    response=$(curl -s https://api.openai.com/v1/chat/completions \
                  -H "Content-Type: application/json" \
                  -H "Authorization: Bearer $OPENAI_API_KEY" \
                  -d "$json_payload")

    echo "API Request finished..."

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
    echo "Type another query or press Ctrl+C to exit."
done
