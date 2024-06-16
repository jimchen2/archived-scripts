import json
import os
import subprocess

# Define the path to your blogs.bson file
input_file_bson = './test/blogs.bson'
input_file = './test/blogs.json'
subprocess.run(["bsondump", input_file_bson, "--outFile", input_file])

# Ensure the directory for documents exists
output_dir = './markdown_documents'
os.makedirs(output_dir, exist_ok=True)

# Process each line (blog entry) in the blogs.json file as a separate JSON object
with open(input_file, 'r') as file:
    for line in file:
        try:
            blog = json.loads(line)
            # Use the blog title as the filename, sanitizing it to be filesystem-friendly
            title = blog['title'].replace(' ', '_').translate({ord(c): "" for c in r'\/:*?"<>|'})
            output_filename = f'{title}.md'
            output_path = os.path.join(output_dir, output_filename)

            # Prepare YAML front matter
            yaml_front_matter = f"""---
title: "{blog['title']}"
date: {blog['date']}
type: {blog['type']}
_oid: "{blog['_id']['$oid']}"
---
"""

            # Convert HTML in the body to Markdown using Pandoc
            process = subprocess.run(
                ['pandoc', '--from=html', '--to=markdown'],
                input=blog["body"].encode('utf-8'),
                capture_output=True
            )
            markdown_body = process.stdout.decode('utf-8')

            # Combine YAML front matter and Markdown body
            full_content = yaml_front_matter + markdown_body
            
            # Write the combined content to a Markdown file
            with open(output_path, 'w') as outfile:
                outfile.write(full_content)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from line: {e}")
        except subprocess.CalledProcessError as e:
            print(f"Error calling Pandoc for line: {e}")

print("Done converting blogs.json into individual Markdown documents with YAML front matter.")

