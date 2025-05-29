import json
import sys
import os
import subprocess
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from logger import get_logger
from modules.data_processing import extract_text_and_links
from modules.process_manager import start_scraping
from modules.persistency import (
    OllamaEmbeddingFunction,
    count_words,
    initialize_chromadb,
    create_collection,
    populate_collection,
    save_many_pages,
    process_query,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def write_json_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def read_json_file(filename):
    with open(filename, 'r') as f:
        return json.load(f)
    
def append_json_file(data, filename):
    try:
        with open(filename, 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []
    existing_data.append(data)
    with open(filename, 'w') as f:
        json.dump(existing_data, f, indent=4)

def scrape_and_save(base_url, max_depth, processes):
    logger = get_logger(__name__)
    logger.info("Starting the web scraping process...")
    pages_raw = start_scraping(base_url, max_depth, extract_text_and_links, processes)
    logger.info(f"Scraping finished. {len(pages_raw)} pages scraped.")

    pages = [(page['url'], page['text']) for page in pages_raw]
    logger.info(f"Saving {len(pages)} pages to the Sqlite database...")
    save_many_pages(pages)
    logger.info("Data saved successfully.")
    
    return pages

def setup_vector_db(pages):
    logger = get_logger(__name__)
    
    logger.info("Starting vector database population...")
    chroma_client = initialize_chromadb()
    embedding_function = OllamaEmbeddingFunction()
    collection = create_collection(chroma_client, "text", embedding_function)
    
    crawled_data = [{"url": url, "content": content} for url, content in pages]
    populate_collection(collection, crawled_data)
    return collection

def interactive_ai_session(collection):
    print("\n" + "="*50)
    print("         AI QUESTION SESSION")
    print("="*50)
    print("Enter your questions (type 'quit' to exit):")
    
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
        if question:
            process_query(collection, question, 6)
        else:
            print("Please enter a valid question.")

def search_words_in_pages(keyword):
    print("\n" + "="*50)
    print("         WORD SEARCH")
    print("="*50)
    print("Enter words to search (type 'quit' to exit):")
    
    wordcount = count_words(keyword)
    print(f"Total words in database: {wordcount}")
def run_streamlit():
    try:
        subprocess.Popen(["streamlit", "run", "src/modules/interface/app.py"])
    except Exception as e:
        print(f"Error running Streamlit: {e}")

def clear_streamlit_files():
    try:
        os.remove("streamlit_in.json")
        os.remove("streamlit_out.json")
    except FileNotFoundError:
        pass

def await_input():
    while True:
        try:
            with open("streamlit_out.json", "r") as f:
                data = json.load(f)
                if data:
                    break
        except FileNotFoundError:
            pass
        time.sleep(1)
    return data

def display_menu():
    print("\n" + "="*50)
    print("         WEB CRAWLER & AI ASSISTANT")
    print("="*50)
    print("1. Run with Streamlit interface")
    print("2. Run terminal mode (scraping only)")
    print("3. Run terminal mode (scraping + AI)")
    print("4. Run terminal mode (scraping + word search)")
    print("5. Exit")
    print("="*50)

def get_user_input():
    base_url = input("Enter base URL: ").strip()
    max_depth = int(input("Enter max depth (default 3): ") or 3)
    processes = int(input("Enter number of processes (default 12): ") or 12)
    return base_url, max_depth, processes

def terminal_mode(use_ai=False, use_search=False):
    base_url, max_depth, processes = get_user_input()
    
    print(f"\nStarting scraping...")
    print(f"URL: {base_url}")
    print(f"Max depth: {max_depth}")
    print(f"Processes: {processes}")
    print(f"AI processing: {'Enabled' if use_ai else 'Disabled'}")
    print(f"Word search: {'Enabled' if use_search else 'Disabled'}")
    
    pages = scrape_and_save(base_url, max_depth, processes)
    
    if use_ai:
        collection = setup_vector_db(pages)
        interactive_ai_session(collection)
    elif use_search:
        keyword = input("Enter word to search: ").strip()
        search_words_in_pages(keyword)
    
    print("\nProcess completed!")

def streamlit_mode():
    clear_streamlit_files()
    run_streamlit()
    data = await_input()
    
    base_url = data.get("base_url")
    max_depth = data.get("max_depth")
    question = data.get("question")
    processes = data.get("processes")
    
    pages = scrape_and_save(base_url, max_depth, processes)
    collection = setup_vector_db(pages)
    process_query(collection, question, 6)

def main():
    while True:
        display_menu()
        choice = input("Select an option (1-5): ").strip()
        
        if choice == "1":
            streamlit_mode()
        elif choice == "2":
            terminal_mode(use_ai=False, use_search=False)
        elif choice == "3":
            terminal_mode(use_ai=True, use_search=False)
        elif choice == "4":
            terminal_mode(use_ai=False, use_search=True)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()