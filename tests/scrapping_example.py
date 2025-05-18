import requests
from bs4 import BeautifulSoup
import time

def extract_text_and_links(url):
    try:
        start = time.time()
        response = requests.get(url, verify=False, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        links = [a['href'] for a in soup.find_all('a', href=True)]
        elapsed = time.time() - start
        print(f"Scraped {url} in {elapsed:.2f}s, found {len(links)} links.")
        return url, text, links
    except Exception as e:
        print(f"Error with {url}: {e}")
        return url, "", []

def start_scraping(base_url, max_depth):
    visited = set()
    results = []

    to_visit = [(base_url, 0)]

    while to_visit:
        url, depth = to_visit.pop(0)

        if url in visited or depth > max_depth:
            continue

        visited.add(url)
        url, text, links = extract_text_and_links(url)
        results.append({'url': url, 'text': text, 'links': links})

        for link in links:
            full_link = base_url + link if link.startswith('/') else link
            if full_link.startswith(base_url) and full_link not in visited:
                to_visit.append((full_link, depth + 1))

    return results

if __name__ == "__main__":
    start_time = time.time()

    depth = 2
    base_url = "https://react.dev"

    scraped_results = start_scraping(base_url, depth)

    total_time = time.time() - start_time

    print("\n=== FINAL RESULTS ===")
    print(f"Scraped {len(scraped_results)} pages in {total_time:.2f} seconds.")
    for entry in scraped_results:
        print(f"URL: {entry['url']}")
        print(f"Links found: {len(entry['links'])}")
        print("-+-" * 40)
