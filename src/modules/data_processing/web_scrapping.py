
import time
import requests
from bs4 import BeautifulSoup
from multiprocessing import current_process


def extract_text_and_links(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }

    try:
        start = time.time()
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        links = [a['href'] for a in soup.find_all('a', href=True)]
        elapsed = time.time() - start
        print(f"[{current_process().name}] Scraped {url} in {elapsed:.2f}s, found {len(links)} links.")
        return url, text, links
    except Exception as e:
        print(f"[{current_process().name}] Error with {url}: {e}")
        return url, "", []
