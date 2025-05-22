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



def setup_vector_db(pages, question):
    logger = get_logger(__name__)
    
    """     search_words = ["react", "React", "React.js", "ReactJS", "reactjs"]
    for word in search_words:
        count = count_words(word)
        logger.info(f"Total words for '{word}': {count}") """
        
    logger.info("Starting vector database population...")
    chroma_client = initialize_chromadb()
    embedding_function = OllamaEmbeddingFunction()
    collection = create_collection(chroma_client, "text", embedding_function)
    
    crawled_data = [{"url": url, "content": content} for url, content in pages]
    populate_collection(collection, crawled_data)
    process_query(collection, question, 6)

def run_streamlit():
    try:
        subprocess.Popen(["streamlit", "run", "src/modules/interface/app.py"])
    except Exception as e:
        print(f"Error running Streamlit: {e}")

def main(base_url, max_depth, question, processes):
  
    write_json_file({"type": "main","base_url": base_url, "max_depth": max_depth, "question": question, "processes": processes}, "streamlit_in.json")
    pages = scrape_and_save(base_url, max_depth, processes)
    setup_vector_db(pages, question)

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
if __name__ == "__main__":
    """ base_url = "https://docs.streamlit.io/"
    max_depth = 3
    question = "O que é um componente?"
    processes = 12
    streamlit = True #TODO: Implemementar opção de rodar o streamlit ou não """
    clear_streamlit_files()
    run_streamlit()
    data = await_input()
    base_url = data.get("base_url")
    max_depth = data.get("max_depth")
    question = data.get("question")
    processes = data.get("processes")


    main(base_url, max_depth, question, processes)