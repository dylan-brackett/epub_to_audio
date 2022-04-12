import os
import re
import sys
import xml.etree.ElementTree as ET
from shutil import rmtree
from zipfile import ZipFile

import pyttsx3

TEMP_DIR = '__epub_to_audio_tmp'

def extract_epub(path_to_epub):
    with ZipFile(path_to_epub) as zip:
        zip.extractall(TEMP_DIR)

def xml_tag_search(root, tag):
    tag_pattern = re.compile(rf'\b{tag}\b', flags=re.IGNORECASE)
    for node in root.iter():
        if tag_pattern.search(node.tag):
            return node

def get_xml_root(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return ET.fromstring(f.read())

def get_root_file(epub_dir):
    container_path = os.path.join(epub_dir, 'META-INF', 'container.xml')
    root = get_xml_root(container_path)
    for item in root.iter():
        if ('rootfile' in item.tag) and (not 'rootfiles' in item.tag):
            return item.get('full-path')

def get_spine_idrefs(spine):
    content_idrefs = []
    for item in list(spine):
        content_idrefs.append(item.get('idref'))
    return content_idrefs

def get_spine(content_path):
    root = get_xml_root(content_path)
    for item in root.iter():
        if 'spine' in item.tag:
            return item

def get_spine_content_chapters(content_path):
    chapters = []

    spine = get_spine(content_path)
    content_idrefs = get_spine_idrefs(spine)
    
    root = get_xml_root(content_path)
    for id in content_idrefs:
        for item in root.iter():
            if item.get('id') == id:
                path = os.path.join(os.path.dirname(content_path), item.get('href'))
                chapters.append(path)
    return chapters

def get_chapter_text(chapter_path):
    root = get_xml_root(chapter_path)
    body = xml_tag_search(root, 'body')
    chapter_text = ''
    for t in body.itertext():
        chapter_text += t
    return chapter_text


def get_epub_text(chapters):
    book_text = ''
    for chapter in chapters:
        book_text += get_chapter_text(chapter)
    return book_text

def print_usage():
    print('Usage: epub_to_audio.py [-o output_file.mp3] FILE')

if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 4:
        print_usage()
        exit()

    path_to_epub = ''
    out_file = ''

    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i].startswith('-o'):
            try:
                out_file = args[i + 1]
            except:
                print_usage()
                exit()
        elif not path_to_epub:
            path_to_epub = args[i]

    if not out_file:
        out_file = path_to_epub.replace('.epub', '.mp3')

    # Remove old tmp dir if needed
    if os.path.exists(TEMP_DIR):
        rmtree(TEMP_DIR)

    # Get the epub text
    extract_epub(path_to_epub)
    print("Extracting Epub...")
    content_path = os.path.join(TEMP_DIR, get_root_file(TEMP_DIR))
    chapters = get_spine_content_chapters(content_path)
    print("Reading text...")
    text = get_epub_text(chapters)
    # text = get_chapter_text(chapters[2])

    # Create mp3
    engine = pyttsx3.init()
    engine.setProperty('rate', 120)
    engine.setProperty('volume', 0.9)
    print("Converting to audio, this may take serveral minutes.")
    engine.save_to_file(text, out_file)
    engine.runAndWait()

    # Delete temp directory
    rmtree(TEMP_DIR)
