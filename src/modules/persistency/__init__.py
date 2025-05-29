# __init__.py

from .text_storage import (
    create_database_file,
    setup_database,
    save_page,
    wipe_database,
    count_words,
    save_many_pages,
)

from .vector_storage import (
    OllamaEmbeddingFunction,
    get_prompt,
    get_ollama_response,
    initialize_chromadb,
    create_collection,
    split_into_chunks,
    populate_collection,
    process_query,

)
__all__ = [
    "create_database_file",
    "setup_database",
    "save_page",
    "wipe_database",
    "count_words",
    "OllamaEmbeddingFunction",
    "get_prompt",
    "get_ollama_response",
    "initialize_chromadb",
    "create_collection",
    "split_into_chunks",
    "populate_collection",
    "process_query",
    "save_many_pages",
]
