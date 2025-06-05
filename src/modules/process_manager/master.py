import multiprocessing
from multiprocessing import Manager, Pool
import time
from .worker import worker

from logger import get_logger

logger = get_logger(__name__)


def normalize_link(link, base_url):
    return base_url + link if link.startswith('/') else link


def worker_wrapper(args):
    url, base_url, function = args
    return worker((url, base_url), function)


def _compute_batch_embeddings(args):
    embedding_function, batch_docs = args
    logger.info(f"Processando batch com {len(batch_docs)} documentos em processo {multiprocessing.current_process().name}")
    embs = embedding_function(batch_docs)
    logger.info(f"Finalizado batch em processo {multiprocessing.current_process().name}")
    return embs


def compute_embeddings_parallel(embedding_function, documents, batch_size=50, processes=None):
    total = len(documents)
    logger.info(f"Iniciando computação paralela de embeddings para {total} documentos, batch_size={batch_size}")
    batches = [
        documents[i : i + batch_size] for i in range(0, total, batch_size)
    ]

    logger.info(f"Total de batches para processar: {len(batches)}")
    args = [(embedding_function, batch) for batch in batches]
    with multiprocessing.Pool(processes=processes) as pool:
        results = pool.map(_compute_batch_embeddings, args)
    embeddings = [emb for batch_embs in results for emb in batch_embs]

    logger.info("Finalizada computação paralela de embeddings para todos os documentos")
    return embeddings


def start_scraping(base_url, max_depth, function, processes=12):
    """
    Start web scraping with multiprocessing
    """
    manager = Manager()
    visited = manager.dict()
    results = manager.list()
    to_visit = manager.list([(base_url, 0)])
    logger.info(f"Starting scraping: {base_url} up to depth {max_depth} with {processes} processes.")
    start = time.time()

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
            current_batch_with_func = [(url, base_url, function) for url, base_url, depth in current_batch]
            output = pool.map(worker_wrapper, current_batch_with_func)

            for (url, depth), (url_result, text, links) in zip([(u, d) for u, _, d in current_batch], output):
                results.append({'url': url_result, 'text': text, 'links': links})
                for link in links:
                    full_link = normalize_link(link, base_url)
                    if full_link.startswith(base_url) and full_link not in visited:
                        next_round.append((full_link, depth + 1))
            to_visit.extend(next_round)

    logger.info(f"Scraping finished. {len(results)} pages scraped. Time taken: {time.time() - start:.2f} seconds.")
    return list(results)