import os
import yaml
import json
import subprocess
import tempfile
from bson import ObjectId

# Directories for your files
markdown_dir = './cn_markdown_documents'
output_json_file = './test/translated_blog.json'

blog_entries = []

lua_filter_code = '''
function Math(elem)
  -- Return the math content wrapped in $$ for display math
  return pandoc.RawInline('html', '$$' .. elem.text .. '$$')
end
function InlineMath(elem)
  -- Return the math content wrapped in $ for inline math
  return pandoc.RawInline('html', '$' .. elem.text .. '$')
end
'''

for root, dirs, files in os.walk(markdown_dir):
    for md_filename in files:
        if md_filename.endswith('.md'):
            md_file_path = os.path.join(root, md_filename)
            html_file_path = os.path.splitext(md_file_path)[0] + '.html'

            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write(lua_filter_code)
                temp_file_path = temp_file.name

            pandoc_command = [
                "pandoc",
                f"--lua-filter={temp_file_path}",
                "--no-highlight",
                md_file_path,
                "-o",
                html_file_path
            ]

            subprocess.run(pandoc_command)

            os.unlink(temp_file_path)

            # Extract YAML metadata from Markdown file
            with open(md_file_path, 'r', encoding='utf-8') as md_file:
                content = md_file.read().split('---', 2)
                if len(content) >= 3:
                    metadata = yaml.safe_load(content[1])  # YAML metadata is between the first two '---'
                else:
                    metadata = {}

            # Read HTML content
            try:
                with open(html_file_path, 'r', encoding='utf-8') as html_file:
                    html_content = html_file.read()
            except FileNotFoundError:
                print(f"HTML file not found for {md_filename}, skipping.")
                continue

            # Create blog entry with metadata and HTML body
            blog_entry = metadata  # Start with YAML metadata
            blog_entry['body'] = html_content  # Add HTML content as 'body'

            # Generate a new ObjectId
            blog_entry['_id'] = str(ObjectId())

            # Add the blog entry to the list
            blog_entries.append(blog_entry)
            os.remove(html_file_path)

# Open and write the file in text mode, with each document on a separate line
with open(output_json_file, 'w', encoding='utf-8') as outfile:
    for entry in blog_entries:
        json.dump(entry, outfile)
        outfile.write('\n')

print(f"Converted Markdown and HTML documents to JSON: {output_json_file}")
