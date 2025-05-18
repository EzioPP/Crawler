from multiprocessing import Manager, Pool
from .worker import worker
from utils import normalize_link
from logger import get_logger

logger = get_logger(__name__)

def worker_wrapper(args):
    url, base_url, function = args
    return worker((url, base_url), function)


def start_scraping(base_url, max_depth, function, processes=12):
    manager = Manager()
    visited = manager.dict()
    results = manager.list()
    to_visit = manager.list([(base_url, 0)])
    logger.info(f"Starting scraping: {base_url} up to depth {max_depth} with {processes} processes.")

    with Pool(processes=processes) as pool:
        while to_visit:
            current_batch = []
            next_round = []
            for url, depth in list(to_visit):
                if url in visited or depth > max_depth:
                    continue
                visited[url] = True
                current_batch.append((url, base_url, depth))
                logger.info(f"Visiting: {url} at depth {depth}")
            to_visit[:] = []

            if not current_batch:
                logger.info("No more URLs to process. Exiting loop.")
                break

            # Passa função junto para o worker_wrapper
            current_batch_with_func = [(url, base_url, function) for url, base_url, depth in current_batch]
            output = pool.map(worker_wrapper, current_batch_with_func)

            for (url, depth), (url_result, text, links) in zip([(u, d) for u, _, d in current_batch], output):
                results.append({'url': url_result, 'text': text, 'links': links})
                logger.info(f"Scraped: {url_result} with {len(links)} links found.")
                for link in links:
                    full_link = normalize_link(link, base_url)
                    if full_link.startswith(base_url) and full_link not in visited:
                        next_round.append((full_link, depth + 1))
            to_visit.extend(next_round)

    logger.info(f"Scraping finished. {len(results)} pages scraped.")
    return list(results)