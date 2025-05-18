import requests
from bs4 import BeautifulSoup
import time
from multiprocessing import Manager, Pool, current_process


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


def worker(args):
    url, base = args
    return extract_text_and_links(url)


def start_scraping(base_url, max_depth):
    manager = Manager()
    visited = manager.dict()
    results = manager.list()

    to_visit = manager.list([(base_url, 0)])

    with Pool(processes=12) as pool:
        while to_visit:
            current_batch = []
            next_round = []

            for url, depth in list(to_visit):
                if url in visited or depth > max_depth:
                    continue
                visited[url] = True
                current_batch.append((url, base_url))

            to_visit[:] = []

            if not current_batch:
                break

            output = pool.map(worker, current_batch)

            for url, text, links in output:
                results.append({'url': url, 'text': text, 'links': links})
                for link in links:
                    full_link = base_url + link if link.startswith('/') else link
                    if full_link.startswith(base_url) and full_link not in visited:
                        next_round.append((full_link, depth + 1))

            to_visit.extend(next_round)

    return list(results)


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
        #print(f"Text Snippet: {entry['text'][:200]}")
        print(f"Links found: {len(entry['links'])}")
        print("-+-" * 40)
