import os
import re

def replace_hyphen_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Ignore the first 5 lines
    new_lines = lines[:5] + [re.sub(r'^-', '- ', line) for line in lines[5:]]

    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)

def traverse_and_replace(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                replace_hyphen_in_file(file_path)
                print(f'Processed {file_path}')

# Set the base directory where the markdown_documents directory is located
base_directory = './cn_markdown_documents'

# Call the function to traverse and replace hyphens in markdown files
traverse_and_replace(base_directory)
