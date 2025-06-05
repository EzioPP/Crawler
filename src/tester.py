import json
import sys
import os
import subprocess
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from logger import get_logger
from modules.data_processing import extract_text_and_links
from modules.process_manager import start_scraping
from modules.persistency import (
    count_words,
    save_many_pages,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CrawlerTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = get_logger(__name__)
        self.results = []
        
    def clear_databases_before_test(self):
        try:
            self.logger.info("Bancos de dados limpos para o teste")
        except Exception as e:
            self.logger.error(f"Erro ao limpar bancos de dados: {e}")
    
    def run_single_test(self, depth, processes):
        test_name = f"profundidade_{depth}_processos_{processes}"
        self.logger.info(f"Iniciando teste: {test_name}")
        
        self.clear_databases_before_test()
        
        start_time = time.time()
        success = False
        pages_scraped = 0
        error_message = None
        
        try:
            pages_raw = start_scraping(self.base_url, depth, extract_text_and_links, processes)
            pages_scraped = len(pages_raw)
            
            pages = [(page['url'], page['text']) for page in pages_raw]
            save_many_pages(pages)
            
            success = True
            self.logger.info(f"Teste {test_name} concluído com sucesso. Páginas coletadas: {pages_scraped}")
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Teste {test_name} falhou: {error_message}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        result = {
            'nome_teste': test_name,
            'profundidade': depth,
            'processos': processes,
            'sucesso': success,
            'paginas_coletadas': pages_scraped,
            'duracao_segundos': round(duration, 2),
            'duracao_minutos': round(duration / 60, 2),
            'mensagem_erro': error_message,
            'timestamp': datetime.now().isoformat(),
            'paginas_por_segundo': round(pages_scraped / duration, 2) if duration > 0 else 0
        }
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        depths = [2,3, 4]
        processes_list = [1,2, 4, 8, 12, 16, 24]
        
        total_tests = len(depths) * len(processes_list)
        current_test = 0
        
        print(f"\n🧪 Iniciando testes abrangentes do crawler")
        print(f"📊 Total de testes para executar: {total_tests}")
        print(f"🌐 URL alvo: {self.base_url}")
        print("=" * 60)
        
        for depth in depths:
            for processes in processes_list:
                current_test += 1
                print(f"\n[{current_test}/{total_tests}] Testando: Profundidade={depth}, Processos={processes}")
                
                result = self.run_single_test(depth, processes)
                
                if result['sucesso']:
                    print(f"✅ SUCESSO: {result['paginas_coletadas']} páginas em {result['duracao_segundos']}s ({result['paginas_por_segundo']} páginas/s)")
                else:
                    print(f"❌ FALHOU: {result['mensagem_erro']}")
                
                time.sleep(2)
        
        print("\n🎉 Todos os testes concluídos!")
        return self.results
    
    def save_results_to_csv(self, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resultados_teste_crawler_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if self.results:
                fieldnames = self.results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
        
        print(f"📄 Resultados salvos em: {filename}")
        return filename
    
    def save_results_to_json(self, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resultados_teste_crawler_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.results, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"📄 Resultados salvos em: {filename}")
        return filename
    
    def print_summary(self):
        if not self.results:
            print("Nenhum resultado de teste para resumir.")
            return
        
        successful_tests = [r for r in self.results if r['sucesso']]
        failed_tests = [r for r in self.results if not r['sucesso']]
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"Total de testes executados: {len(self.results)}")
        print(f"Bem-sucedidos: {len(successful_tests)}")
        print(f"Falharam: {len(failed_tests)}")
        
        if successful_tests:
            print("\n🏆 MÉTRICAS DE PERFORMANCE (apenas testes bem-sucedidos):")
            
            best_pages = max(successful_tests, key=lambda x: x['paginas_coletadas'])
            print(f"Mais páginas coletadas: {best_pages['paginas_coletadas']} (Profundidade: {best_pages['profundidade']}, Processos: {best_pages['processos']})")
            
            best_speed = max(successful_tests, key=lambda x: x['paginas_por_segundo'])
            print(f"Coleta mais rápida: {best_speed['paginas_por_segundo']} páginas/s (Profundidade: {best_speed['profundidade']}, Processos: {best_speed['processos']})")
            
            fastest_time = min(successful_tests, key=lambda x: x['duracao_segundos'])
            print(f"Menor duração: {fastest_time['duracao_segundos']}s (Profundidade: {fastest_time['profundidade']}, Processos: {fastest_time['processos']})")
            
            print(f"\nMédia de páginas coletadas: {sum(r['paginas_coletadas'] for r in successful_tests) / len(successful_tests):.1f}")
            print(f"Duração média: {sum(r['duracao_segundos'] for r in successful_tests) / len(successful_tests):.1f}s")
            print(f"Velocidade média: {sum(r['paginas_por_segundo'] for r in successful_tests) / len(successful_tests):.1f} páginas/s")
        
        if failed_tests:
            print(f"\n❌ TESTES QUE FALHARAM:")
            for test in failed_tests:
                print(f"  - {test['nome_teste']}: {test['mensagem_erro']}")
        
        print("=" * 60)

def main():
    print("🕷️  Ferramenta de Teste de Performance do Web Crawler")
    print("=" * 50)
    
    base_url = input("Digite a URL alvo para teste: ").strip()
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    print(f"\n📋 Configuração do Teste:")
    print(f"   URL: {base_url}")
    print(f"   Profundidades para testar: 2, 4")
    print(f"   Processos para testar: 2, 4, 8, 12, 16, 24")
    print(f"   Total de testes: 12")
    
    confirm = input("\nProsseguir com os testes? (S/n): ").strip().lower()
    if confirm in ['n', 'nao', 'não']:
        print("Testes cancelados.")
        return
    
    tester = CrawlerTester(base_url)
    
    try:
        results = tester.run_all_tests()
        
        tester.save_results_to_csv()
        tester.save_results_to_json()
        
        tester.print_summary()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário")
        if tester.results:
            print("Salvando resultados parciais...")
            tester.save_results_to_csv()
            tester.print_summary()
    except Exception as e:
        print(f"\n❌ Testes falharam com erro: {e}")
        if tester.results:
            print("Salvando resultados parciais...")
            tester.save_results_to_csv()

if __name__ == "__main__":
    main()