import os
import sys
import multiprocessing

import chromadb
import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from logger import get_logger

logger = get_logger(__name__)

MODEL = "llama3.2"


class OllamaEmbeddingFunction:
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        logger.info(f"Iniciando geração de embeddings para batch de tamanho {len(input)}")
        for idx, text in enumerate(input):
            logger.debug(f"Gerando embedding para texto {idx + 1}/{len(input)}")
            response = ollama.embeddings(model=self.model_name, prompt=text)
            embeddings.append(response["embedding"])
        logger.info("Finalizada geração de embeddings para batch")
        return embeddings


def _compute_batch_embeddings(args):
    embedding_function, batch_docs = args
    logger.info(f"Processando batch com {len(batch_docs)} documentos em processo {multiprocessing.current_process().name}")
    embs = embedding_function(batch_docs)
    logger.info(f"Finalizado batch em processo {multiprocessing.current_process().name}")
    return embs


def compute_embeddings_parallel(embedding_function, documents, batch_size=30):
    total = len(documents)
    logger.info(f"Iniciando computação paralela de embeddings para {total} documentos, batch_size={batch_size}")

    batches = [
        documents[i : i + batch_size] for i in range(0, total, batch_size)
    ]

    logger.info(f"Total de batches para processar: {len(batches)}")

    args = [(embedding_function, batch) for batch in batches]

    with multiprocessing.Pool() as pool:
        results = pool.map(_compute_batch_embeddings, args)

    embeddings = [emb for batch_embs in results for emb in batch_embs]

    logger.info("Finalizada computação paralela de embeddings para todos os documentos")
    return embeddings


def get_prompt(query, context):
    return f"""
    Baseado no texto, responda a pergunta a seguir.
    {context}
    Pergunta: {query}
    Resposta:
    """


def get_ollama_response(query, context, model=MODEL):
    prompt = get_prompt(query, context)
    logger.info(f"Gerando resposta para a query: {query}")
    logger.debug(f"Prompt enviado para modelo:\n{prompt}")
    print(f"Prompt: {prompt}")
    input("Pressione Enter para continuar...")
    response = ollama.generate(model=model, prompt=prompt)
    logger.info(f"Resposta gerada para a query: {query}")
    return response["response"]


def initialize_chromadb():
    try:
        logger.info("Inicializando cliente ChromaDB...")
        client = chromadb.Client()
        logger.info("Cliente ChromaDB inicializado com sucesso")
        return client
    except Exception as e:
        logger.error(f"Erro ao inicializar o cliente ChromaDB: {e}")


def create_collection(client, collection_name, embedding_function):
    try:
        logger.info(f"Criando coleção '{collection_name}'...")
        collection = client.create_collection(
            collection_name, embedding_function=embedding_function
        )
        logger.info(f"Coleção '{collection_name}' criada com sucesso")
        return collection
    except Exception as e:
        logger.error(f"Erro ao criar a coleção: {e}")


def split_into_chunks(crawled_data, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )

    all_chunks = []
    all_metadatas = []
    all_ids = []

    logger.info(f"Iniciando divisão dos dados em chunks com chunk_size={chunk_size}, overlap={chunk_overlap}")

    for i, entry in enumerate(crawled_data):
        logger.info(f"Processando documento {i + 1}/{len(crawled_data)}: {entry['url']}")
        chunks = text_splitter.split_text(entry["content"])

        for j, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "source": entry["url"],
                "doc_id": i,
                "chunk_index": j
            })
            all_ids.append(f"doc_{i}_chunk_{j}")

    logger.info(f"Divisão concluída. Total de chunks gerados: {len(all_chunks)}")
    return all_chunks, all_metadatas, all_ids


def batch_add(collection, documents, metadatas, ids, embeddings, batch_size=200):
    total = len(documents)
    logger.info(f"Iniciando adição em batch dos documentos na coleção, total={total}, batch_size={batch_size}")

    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        logger.info(f"Adicionando batch: {start_idx} até {end_idx}")

        batch_docs = documents[start_idx:end_idx]
        batch_meta = metadatas[start_idx:end_idx]
        batch_ids = ids[start_idx:end_idx]
        batch_embs = embeddings[start_idx:end_idx]

        collection.add(
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids,
            embeddings=batch_embs,
        )
        logger.info(f"Batch adicionado: {start_idx} até {end_idx}")

    logger.info("Adição em batch concluída")


def populate_collection(collection, crawled_data):
    chunks, metadatas, ids = split_into_chunks(crawled_data)
    logger.info(f"Total de chunks: {len(chunks)}")

    embedding_function = OllamaEmbeddingFunction()
    embeddings = compute_embeddings_parallel(embedding_function, chunks, batch_size=30)
    batch_add(collection, chunks, metadatas, ids, embeddings, batch_size=200)

    logger.info(f"Adicionado total de {len(chunks)} chunks na coleção.")


def get_mock_data():
    return [
        {
            "url": "https://pt.wikipedia.org/wiki/Venceslau_IV_da_Bo%C3%AAmia",
            "content": "Venceslaus nasceu na cidade imperial de Nurembergue, filho do imperador Carlos IV com sua terceira esposa, Anna von Schweidnitz, descendente da dinastia Piast da Silésia e batizado na igreja de St. Sebaldus. Foi criado pelos arcebispos de Praga, Arnošt de Pardubice e Jan Očko z Vlašimi. Seu pai o coroou em 1363, com apenas dois anos de idade, Rei da Boêmia."
        },
        # Adicione seus outros dados aqui...
    ]


def process_query(collection, query_text, ammount=3):
    results = collection.query(
        query_texts=[query_text],
        n_results=ammount,
        include=["documents", "metadatas", "distances"],
    )
    print("-+-" * 20)
    logger.info(f"Consulta: {results}")
    input()
    if results and len(results["documents"]) > 0:
        documents = results["documents"]
        metadatas = results["metadatas"]

        context = ""
        for doc, meta in zip(documents[0], metadatas[0]):
            url = meta.get("source", "URL desconhecida")
            context += f"Fonte: {url}\nConteúdo: {doc}\n\n"

        metadata = results["metadatas"]
        print("Sending", query_text, context)
        input("Pressione Enter para continuar...")
        response = get_ollama_response(query_text, context)
        logger.info(f"Resposta para a pergunta '{query_text}': {response}")
        logger.info(f"Contexto: {context}")
        logger.info(f"Metadata: {metadata}")
    else:
        logger.warning(f"Nenhum resultado encontrado para a consulta: {query_text}")


def get_questions():
    return [
        {"question": "Qual é o conteúdo do documento?"},
        {"question": "Qual é o URL do documento?"},
        {"question": "Qual é o nome do rei da Boêmia?"},
        {"question": "Qual é a missão principal do F-22 Raptor?"},
        {"question": "Quem fabricou o F-22 Raptor?"},
    ]


def process_all_queries(collection, questions):
    for query in questions:
        query_text = query["question"]
        process_query(collection, query_text)
    logger.info("Processamento de consultas concluído")


def main():
    client = initialize_chromadb()
    embedding_function = OllamaEmbeddingFunction()
    collection = create_collection(client, "text_collection", embedding_function)
    mock_data = get_mock_data()
    populate_collection(collection, mock_data)
    logger.info("Coleção criada e populada com dados de exemplo")
    questions = get_questions()
    process_all_queries(collection, questions)
    logger.info("Resultado salvo no banco de dados")
    logger.info("Processamento concluído")


if __name__ == "__main__":
    main()
