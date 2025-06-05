import json
import sys
import os
import subprocess
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from logger import get_logger
from modules.data_processing import extract_text_and_links
from modules.process_manager import start_scraping
from modules.persistency import (
    OllamaEmbeddingFunction,
    count_words,
    initialize_chromadb,
    create_collection,
    populate_collection,
    save_many_pages,
    process_query,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_and_save(base_url, max_depth, processes, vector_db_enabled=True):
    logger = get_logger(__name__)
    logger.info("Starting the web scraping process...")
    pages_raw = start_scraping(base_url, max_depth, extract_text_and_links, processes)
    logger.info(f"Scraping finished. {len(pages_raw)} pages scraped.")
    pages = [(page['url'], page['text']) for page in pages_raw]
    logger.info(f"Saving {len(pages)} pages to the Sqlite database...")
    save_many_pages(pages)
    logger.info("Data saved successfully.")
    return pages

def setup_vector_db(pages):
    logger = get_logger(__name__)
    logger.info("Starting vector database population...")
    chroma_client = initialize_chromadb()
    embedding_function = OllamaEmbeddingFunction()
    collection = create_collection(chroma_client, "text", embedding_function)
    crawled_data = [{"url": url, "content": content} for url, content in pages]
    populate_collection(collection, crawled_data)
    logger.info("Process completed successfully!")
    return collection

def clear_databases():
    logger = get_logger(__name__)
    try:
        logger.info("Databases cleared successfully!")
    except Exception as e:
        logger.error(f"Error clearing databases: {e}")
        print(f"✗ Erro ao limpar bancos de dados: {e}")

def search_word(word):
    logger = get_logger(__name__)
    try:
        logger.info(f"Searching for word: {word}")
        print(f"Procurando por '{word}' nos dados coletados...")
        results = count_words(word)
        if results:
            print(f"✓ Palavra '{word}' encontrada {results} vezes.")
        else:
            print(f"✗ Palavra '{word}' não encontrada nos dados coletados.")
    except Exception as e:
        logger.error(f"Error searching for word: {e}")
        print(f"✗ Erro ao procurar palavra: {e}")

def ai_query(collection, query):
    logger = get_logger(__name__)
    try:
        if collection is None:
            print("✗ IA não está habilitada. Execute o scraping com IA primeiro.")
            return
        logger.info(f"Processing AI query: {query}")
        result = process_query(collection, query)
        print(f"Resultado da Consulta IA: {result}")
    except Exception as e:
        logger.error(f"Error processing AI query: {e}")
        print(f"✗ Erro ao processar consulta IA: {e}")

def get_scraping_mode():
    print("\n=== MODO DE COLETA ===")
    print("1. Web scraping com IA (Banco de Dados Vetorial)")
    print("2. Web scraping sem IA (SQLite apenas)")
    
    while True:
        choice = input("Escolha o modo de coleta (1-2): ").strip()
        if choice == "1":
            return True
        elif choice == "2":
            return False
        else:
            print("Escolha inválida. Digite 1 ou 2.")

def get_scraping_parameters():
    print("\n=== PARÂMETROS DE COLETA ===")
    
    base_url = input("Digite a URL do site para coletar: ").strip()
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    while True:
        try:
            max_depth = int(input("Digite o nível máximo de profundidade (ex: 2): ").strip())
            break
        except ValueError:
            print("Digite um número válido para a profundidade.")
    
    while True:
        try:
            processes = int(input("Digite o número de processos (ex: 4): ").strip())
            break
        except ValueError:
            print("Digite um número válido para processos.")
    
    return base_url, max_depth, processes

def main_menu(collection=None):
    while True:
        print("\n" + "="*50)
        print("           MENU WEB CRAWLER")
        print("="*50)
        print("1. Buscar uma palavra nos dados coletados")
        if collection is not None:
            print("2. Consulta IA (Busca vetorial)")
        else:
            print("2. Consulta IA (Indisponível - IA não habilitada)")
        print("3. Limpar todos os bancos de dados")
        print("4. Sair")
        print("="*50)
        
        choice = input("Escolha uma opção (1-4): ").strip()
        
        if choice == "1":
            word = input("Digite a palavra para buscar: ").strip()
            if word:
                search_word(word)
        
        elif choice == "2":
            if collection is not None:
                query = input("Digite sua consulta IA: ").strip()
                if query:
                    ai_query(collection, query)
            else:
                print("✗ Consultas IA não estão disponíveis. Execute o scraping com IA habilitada primeiro.")
        
        elif choice == "3":
            confirm = input("Tem certeza que deseja limpar todos os bancos de dados? (s/N): ").strip().lower()
            if confirm == 's':
                clear_databases()
        
        elif choice == "4":
            print("Até logo!")
            break
        
        else:
            print("Escolha inválida. Digite 1-4.")

def main():
    logger = get_logger(__name__)
    collection = None
    
    print("🕷️  Bem-vindo ao Aplicativo Web Crawler!")
    
    vector_db_enabled = get_scraping_mode()
    
    base_url, max_depth, processes = get_scraping_parameters()
    
    print(f"\n=== INICIANDO COLETA ===")
    print(f"URL: {base_url}")
    print(f"Profundidade Máxima: {max_depth}")
    print(f"Processos: {processes}")
    print(f"IA Habilitada: {'Sim' if vector_db_enabled else 'Não'}")
    
    try:
        pages = scrape_and_save(base_url, max_depth, processes, vector_db_enabled)
        
        if vector_db_enabled:
            collection = setup_vector_db(pages)
            print("✓ Coleta com IA concluída com sucesso!")
        else:
            print("✓ Coleta concluída com sucesso!")
        
        main_menu(collection)
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        print(f"✗ Erro: {e}")

if __name__ == "__main__":
    main()
