# Crawler

## Descrição

Este é um sistema de web crawler inteligente que combina raspagem de dados web com processamento de IA para análise de conteúdo. O sistema oferece múltiplas interfaces de uso e capacidades de busca avançada.

## Funcionalidades

- **Web Scraping Paralelo**: Extração eficiente de conteúdo de múltiplas páginas web
- **Processamento com IA**: Análise inteligente de conteúdo usando embeddings e modelos de linguagem
- **Banco de Dados Vetorial**: Armazenamento e busca semântica usando ChromaDB
- **Modo Terminal**: Operação via linha de comando para automação
- **Busca de Palavras**: Funcionalidade de contagem e busca de termos específicos


### Opções de Execução

1. **Modo Terminal (apenas scraping)**: Extração de dados sem processamento IA
2. **Modo Terminal (scraping + IA)**: Extração e análise com IA
3. **Modo Terminal (scraping + busca)**: Extração e busca de palavras
4. **Sair**: Encerrar o programa


## Configuração

- **URL Base**: URL inicial para começar o scraping
- **Profundidade Máxima**: Número máximo de níveis de links a seguir
- **Processos**: Número de processos paralelos para scraping
- **IA**: Ativação do processamento com inteligência artificial

## Dependências Principais

- `chromadb`: Banco de dados vetorial
- `urllib3`: Requisições HTTP
- `concurrent.futures`: Processamento paralelo