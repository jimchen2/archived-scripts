import boto3
import base64
import os
from concurrent.futures import ThreadPoolExecutor

def translate_document(content, source_lang, target_lang, content_type):
    client = boto3.client('translate')
    response = client.translate_document(
        Document={
            'Content': base64.b64decode(content),
            'ContentType': content_type
        },
        SourceLanguageCode=source_lang,
        TargetLanguageCode=target_lang
    )
    return response['TranslatedDocument']['Content']

def process_file(file, root, input_directory, output_directory, source_lang, target_lang):
    input_file_path = os.path.join(root, file)
    with open(input_file_path, 'rb') as f:
        content = f.read()

    content_base64 = base64.b64encode(content).decode('utf-8')
    
    try:
        translated_content = translate_document(content_base64, source_lang, target_lang, 'text/plain')
        
        relative_path = os.path.relpath(input_file_path, input_directory)
        output_file_path = os.path.join(output_directory, relative_path)
        output_file_dir = os.path.dirname(output_file_path)
        
        if not os.path.exists(output_file_dir):
            os.makedirs(output_file_dir)
        
        with open(output_file_path, 'wb') as f:
            f.write(translated_content)
        
        print(f'Translated {file} and saved to {output_file_path}')
    except Exception as e:
        print(f'Failed to translate {file}: {e}')

def translate_markdown_files(input_directory, output_directory, source_lang, target_lang):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    with ThreadPoolExecutor() as executor:
        for root, _, files in os.walk(input_directory):
            futures = [executor.submit(process_file, file, root, input_directory, output_directory, source_lang, target_lang) for file in files if file.endswith('.md')]
            
if __name__ == '__main__':
    input_directory = './markdown_documents'
    output_directory = './cn_markdown_documents'
    source_lang = 'en'
    target_lang = 'zh'  # Chinese language code
    
    translate_markdown_files(input_directory, output_directory, source_lang, target_lang)
