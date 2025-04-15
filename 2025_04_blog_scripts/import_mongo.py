import os
import pymongo
from dotenv import load_dotenv
import subprocess
import tempfile
from datetime import datetime
from bs4 import BeautifulSoup

class Utils():
    def parse_markdown_metadata(content):
        """Manually parse frontmatter from markdown content"""
        metadata = {}
        body = content
        if content.startswith('---'):
            try:
                end_idx = content.index('---', 3)
                metadata_lines = content[3:end_idx].strip().split('\n')
                for line in metadata_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                body = content[end_idx + 3:].strip()
            except ValueError:
                body = content
        return metadata, body

    def count_words(html_text):
        soup = BeautifulSoup(html_text, 'html.parser')
        text_content = soup.get_text(separator=' ')
        return len(text_content.strip().split())

    def process_markdown_file(file_path, language, post_type):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata, body = Utils.parse_markdown_metadata(content)
        if not metadata:
            return None
        title = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            date_obj = datetime.strptime(str(metadata.get('date', '')), '%Y%m%d') if metadata.get('date') else None
        except ValueError:
            date_obj = None

        html_body = Utils.convert_markdown_to_html(body)
        
        return {
            "uuid": metadata.get('uuid', ''),
            "title": title,
            "date": date_obj,
            "type": post_type,
            "body": html_body,
            "language": language,
            "word_count": Utils.count_words(html_body),
            "filename": os.path.basename(file_path)
        }

    def convert_markdown_to_html(markdown_content):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as md_file:
            md_file.write(markdown_content)
            md_file.flush()
            try:
                with tempfile.NamedTemporaryFile(suffix='.lua', delete=False) as lua_file:
                    lua_file.write("""
                    function Math(elem)
                        return pandoc.RawInline('html', '$$' .. elem.text .. '$$')
                    end
                    function InlineMath(elem)
                        return pandoc.RawInline('html', '$' .. elem.text .. '$')
                    end
                    """.encode('utf-8'))
                    lua_filter_path = lua_file.name

                try:
                    result = subprocess.run(
                        ["pandoc", f"--lua-filter={lua_filter_path}", "--no-highlight", 
                         "-f", "markdown", "-t", "html", md_file.name],
                        capture_output=True, text=True, check=True
                    )
                finally:
                    if os.path.exists(lua_filter_path):
                        os.remove(lua_filter_path)

                return result.stdout
            finally:
                os.unlink(md_file.name)

    def determine_language_and_type(relative_path):
        parts = relative_path.split(os.sep)
        filename = parts[-1]
        if filename.startswith('.') or not filename.lower().endswith('.md'):
            return None, None
        language = 'en'
        if len(parts) >= 3 and parts[-3] in ['ru', 'zh', 'de']:
            language = parts[-3]
        content_type = parts[-2] if len(parts) >= 2 else None
        return language, content_type

def main():
    all_posts_data = []
    lang_stats = {}
    total_files = 0
    total_words = 0

    for root, _, files in os.walk('.', topdown=True):
        for file in files:
            full_path = os.path.join(root, file)
            language, post_type = Utils.determine_language_and_type(full_path)

            if language and post_type:
                post_data = Utils.process_markdown_file(full_path, language, post_type)
                if post_data:
                    all_posts_data.append(post_data)
                    total_files += 1
                    total_words += post_data['word_count']

                    # Initialize language stats if not present
                    if language not in lang_stats:
                        lang_stats[language] = {
                            'files': 0,
                            'words': 0,
                            'posts': []
                        }
                    
                    # Update language stats
                    lang_stats[language]['files'] += 1
                    lang_stats[language]['words'] += post_data['word_count']
                    lang_stats[language]['posts'].append({
                        'filename': post_data['filename'],
                        'words': post_data['word_count']
                    })

    # Print statistics
    print("\n=== Statistics by Language ===")
    for lang, stats in lang_stats.items():
        word_percentage = (stats['words'] / total_words * 100) if total_words > 0 else 0
        print(f"\n{lang.upper()} Statistics:")
        print(f"Files: {stats['files']}")
        print(f"Words: {stats['words']} ({word_percentage:.2f}%)")
        
        print("\nTop posts by word count:")
        for post in sorted(stats['posts'], key=lambda x: x['words'], reverse=True)[:20]:
            print(f"- {post['filename']}: {post['words']} words")

    print("\n=== Total Statistics ===")
    print(f"Total Files: {total_files}")
    print(f"Total Words: {total_words}")

    # Rest of the MongoDB processing
    local_uuids = set(post.get("uuid", "") for post in all_posts_data if post.get("uuid"))
    if len(all_posts_data) != len(local_uuids):
        raise ValueError("Duplicate UUID")
    
    load_dotenv()
    client = pymongo.MongoClient(os.getenv('MONGO_URI'))
    collection = client.get_default_database()["blogs"]

    mongo_uuids = set(doc['uuid'] for doc in collection.find({}, {'uuid': 1}))
    if deleted_uuids := mongo_uuids - local_uuids:
        collection.delete_many({'uuid': {'$in': list(deleted_uuids)}})
    
    for post in all_posts_data:
        document = {
            "uuid": post.get("uuid", ""),
            "title": post.get("title", ""),
            "date": post.get("date", None),
            "type": post.get("type", ""),
            "body": post.get("body", ""),
            "language": post.get("language", "en"),
            "word_count": post.get("word_count", 0)
        }
        collection.update_one(
            {"uuid": document["uuid"]},
            {"$set": document},
            upsert=True 
        )
        print(f'\nProcessed {post.get("title", "")}.')

    print(f"\nProcessed {len(all_posts_data)} markdown files.")

if __name__ == "__main__":
    main()