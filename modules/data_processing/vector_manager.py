import os
import sys
import time

import chromadb
import ollama
from logger import get_logger

logger = get_logger(__name__)

MODEL = "llama3.2"


class OllamaEmbeddingFunction:
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name

    def __call__(self, input):
        embeddings = []
        for text in input:
            response = ollama.embeddings(model=self.model_name, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings


class OpenAIEmbeddingFunction:
    # TODO: implementar
    pass


def get_prompt(query, context):
    return f"""
    Baseado no texto, responda a pergunta a seguir.
    Texto: {context}
    Pergunta: {query}
    Resposta:
    """


def get_ollama_response(query, context, model=MODEL):
    prompt = get_prompt(query, context)
    response = ollama.generate(model=model, prompt=prompt)
    return response["response"]


def initialize_chromadb():
    try:
        client = chromadb.Client()
        return client
    except Exception as e:
        logger.error(f"Erro ao inicializar o cliente ChromaDB: {e}")
        sys.exit(1)


def create_collection(client, collection_name, embedding_function):
    try:
        collection = client.create_collection(
            collection_name, embedding_function=embedding_function
        )
        return collection
    except Exception as e:
        logger.error(f"Erro ao criar a coleção: {e}")
        sys.exit(1)


def populate_collection(collection, crawled_data):
    documents = [entry["content"] for entry in crawled_data]
    metadatas = [{"source": entry["url"], "doc_id": i} for i, entry in enumerate(crawled_data)]
    ids = [f"doc_{i}" for i in range(len(crawled_data))]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)



def process_queries(collection, questions):
    responses = []

    for question_query in questions:
        question = question_query["question"]
        query = " ".join(question_query["query"])
        results = collection.query(query_texts=[query], n_results=3)

        logger.info(f"Pergunta: {question}")

        with open("querys.txt", "a") as f:
            f.write("Pergunta: " + question + "\n")
            f.write("Query: " + query + "\n")
            f.write("Documento recuperado:\n")
            for doc in results['documents'][0]:
                f.write(doc + "\n")
            f.write("\n")

        context = "\n".join(results['documents'][0])
        response = get_ollama_response(question, context)
        responses.append(f"{len(responses) + 1}. {response}")

        logger.info("Obtido resposta do Ollama")
        with open("output.txt", "a") as f:
            f.write("Resposta do Ollama:\n")
            f.write(response + "\n")
            f.write("_" * 50 + "\n")

    return responses








def main():
    global chunks, QUESTIONS_QUERYS, file_path, start_time
    start_time = time.time()
    client = initialize_chromadb()
    embedding_function = OllamaEmbeddingFunction()
    collection = create_collection(client, "text_collection", embedding_function)

    populate_collection(collection, chunks, file_path)
    responses = process_queries(collection, QUESTIONS_QUERYS, file_path)

    logger.info("Obtidas todas as respostas do Ollama")
    final_time = time.time() - start_time

    logger.info("Resposta Final:")

    client.delete_collection("text_collection")
    logger.info("Coleção excluída")
    logger.info(f"Processamento do arquivo {file_path} concluído")
    logger.info(f"Tempo total: {final_time:.2f} segundos")


    logger.info(f"Status: {status}")


    logger.info("Resultado salvo no banco de dados")
    logger.info("Processamento concluído")


if __name__ == "__main__":
    main()
