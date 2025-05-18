
import time
import requests
from bs4 import BeautifulSoup
from multiprocessing import current_process
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_text_and_links(url):
    try:
        start = time.time()
        response = requests.get(url, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        links = [a['href'] for a in soup.find_all('a', href=True)]
        elapsed = time.time() - start
        print(f"[{current_process().name}] Scraped {url} in {elapsed:.2f}s, found {len(links)} links.")
        return url, text, links
    except Exception as e:
        print(f"[{current_process().name}] Error with {url}: {e}")
        return url, "", []
