import os
import json
import subprocess
import tempfile
from bson import ObjectId
from datetime import datetime

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
                content = md_file.read()
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) > 2:
                        metadata_str = parts[1].strip()
                    else:
                        metadata_str = ''
                else:
                    metadata_str = ''

            # Print the extracted metadata for debugging
            print(f"Metadata for {md_filename}: {metadata_str}")

            # Extract title, date, and type using string methods
            title_start = metadata_str.find('标题：')
            if title_start != -1:
                title_end = metadata_str.find('\n', title_start)
                if title_end != -1:
                    title = metadata_str[title_start + 3:title_end].strip().strip('"')
                else:
                    title = metadata_str[title_start + 3:].strip().strip('"')
            else:
                title = ''
                
            title = title.replace('“', '').replace('”', '')


            date = metadata_str[metadata_str.find('日期：') + 3:].split('\n')[0].strip()
            


            parts = date.replace('年', ' ').replace('月', ' ').replace('日', ' ').split()
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            time = parts[4] 
            hour, minute, second = map(int, time.split(':'))

# Create the datetime object from the extracted components
            date_object = datetime(year, month, day, hour, minute, second)

# Print the formatted date
            date = date_object.strftime('%a %b %d %Y %H:%M:%S')


            entry_type = metadata_str[metadata_str.find('类型：') + 3:].split('\n')[0].strip()

            # Print extracted values for debugging
            print(f"title: {title}, date: {date}, type: {entry_type}")

            # Ensure all values are correctly extracted
            if not title or not date or not entry_type:
                print(f"Missing metadata in {md_filename}: {metadata_str}")
                continue

            # Read HTML content
            try:
                with open(html_file_path, 'r', encoding='utf-8') as html_file:
                    html_content = html_file.read()
            except FileNotFoundError:
                print(f"HTML file not found for {md_filename}, skipping.")
                continue

            # Create blog entry with metadata and HTML body
            blog_entry = {
                'title': title,
                'date': date,
                'type': entry_type,
                'body': html_content,
                '_id': str(ObjectId())
            }


            # Add the blog entry to the list
            blog_entries.append(blog_entry)
            os.remove(html_file_path)

# Open and write the file in text mode, with each document on a separate line
with open(output_json_file, 'w', encoding='utf-8') as outfile:
    for entry in blog_entries:
        json.dump(entry, outfile, ensure_ascii=False)
        outfile.write('\n')

print(f"Converted Markdown and HTML documents to JSON: {output_json_file}")
