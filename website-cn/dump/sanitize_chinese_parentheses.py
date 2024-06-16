import os

def sanitize_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Replace Chinese full stops with English periods
    sanitized_content = content.replace('。', '.')
    # Replace Chinese parentheses with English parentheses
    sanitized_content = sanitized_content.replace('（', '(').replace('）', ')')
    # Replace ] ( with ](
    sanitized_content = sanitized_content.replace('] (', '](')

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(sanitized_content)

def traverse_and_sanitize(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                sanitize_file(file_path)
                print(f'Processed {file_path}')

# Set the base directory where the markdown documents directory is located
base_directory = './cn_markdown_documents'

# Call the function to traverse and sanitize markdown files
traverse_and_sanitize(base_directory)
