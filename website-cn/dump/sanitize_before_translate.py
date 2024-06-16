import os
import re

def remove_language_identifier_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    cleaned_content = re.sub(r'```[a-zA-Z]*\n', '```\n', content)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)

def traverse_and_clean(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                remove_language_identifier_from_file(file_path)
                print(f'Processed {file_path}')

# Set the base directory where the markdown_documents directory is located
base_directory = './markdown_documents'

# Call the function to traverse and clean markdown files
traverse_and_clean(base_directory)
