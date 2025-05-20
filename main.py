from logger import get_logger
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from data_processing import *
from process_manager import * 
from persistency import (
    OllamaEmbeddingFunction,
    count_words,
    initialize_chromadb,
    create_collection,
    populate_collection,
    save_many_pages,
    process_query,
)

# Abaixo é opcional, mas se tirar o console é spammado com avisos de SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    logger = get_logger(__name__)
    logger.info("Starting the web scraping process...")

    base_url = "https://react.dev"
    max_depth = 1
    processes = 12
    pages_raw = start_scraping(base_url, max_depth, extract_text_and_links, processes)
    logger.info(f"Scraping finished. {len(pages_raw)} pages scraped.")

    pages = [(page['url'], page['text']) for page in pages_raw]
    logger.info(f"Saving {len(pages)} pages to the Sqlite database...")
    save_many_pages(pages)
    logger.info("Data saved successfully.")

    search_words = ["react", "React", "React.js", "ReactJS", "reactjs"]
    for word in search_words:
        count = count_words(word)
        logger.info(f"Total words for '{word}': {count}")

    logger.info("Starting vector database population...")
    chroma_client = initialize_chromadb()
    logger.info("ChromaDB client initialized successfully.")
    embedding_function = OllamaEmbeddingFunction()
    logger.info("Embedding function initialized successfully.")
    collection = create_collection(chroma_client, "text", embedding_function)
    logger.info("Collection created successfully.")
    crawled_data = [{"url": url, "content": content} for url, content in pages]
    logger.info(f"Populating collection with {len(crawled_data)} documents...")
    populate_collection(collection, crawled_data)
    logger.info("Vector database updated successfully.")
    process_query(collection, "what is React?", 3)
    logger.info("Query processed successfully.")


if __name__ == "__main__":
    main()