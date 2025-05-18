import requests
from bs4 import BeautifulSoup

def extract_text_and_links(url):
    try:
        response = requests.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        links = [a['href'] for a in soup.find_all('a', href=True)]
        return text, links

    except Exception as e:
        print(f"Error fetching or parsing URL: {e}")
        return "", []

def recursive_scrape(url, depth, base, results, visited):
    if depth == 0 or url in visited:
        return

    visited.add(url)

    text, links = extract_text_and_links(url)

    results.append({
        'url': url,
        'text': text,
        'links': links
    })

    print(f"Depth: {depth}")
    print(f"Scraped: {url}")
    print(f"Found {len(links)} links.\n")

    for link in links:
        full_link = base + link if link.startswith('/') else link
        if full_link.startswith(base) and full_link not in visited:
            recursive_scrape(full_link, depth - 1, base, results, visited)

if __name__ == "__main__":
    depth = 2
    url = 'https://react.dev'
    base = 'https://react.dev'

    results = []
    visited = set()  # Track visited URLs

    recursive_scrape(url, depth, base, results, visited)

    print("\n\n=== FINAL RESULTS ===")
    for entry in results:
        print(f"URL: {entry['url']}")
        #print(f"Text Snippet: {entry['text'][:200]}")
        print(f"Number of Links: {len(entry['links'])}")
        print("-" * 40)
