from logger import get_logger
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from data_processing import *
from process_manager import * 
def main():
    logger = get_logger(__name__)
    logger.info("Starting the web scraping process...")
    base_url = "https://react.dev"
    max_depth = 2
    processes = 12
    results = start_scraping(base_url, max_depth, extract_text_and_links, processes)
    logger.info(f"Scraping finished. {len(results)} pages scraped.")
if __name__ == "__main__":
    main()