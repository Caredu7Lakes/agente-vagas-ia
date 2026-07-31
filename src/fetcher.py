import os
import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    print("⚠️ Biblioteca 'bs4' não encontrada. Instale com: pip install beautifulsoup4")
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class JobFetcher:
    def __init__(self):
        # Palavras-chave detalhadas
        self.keywords = [
            "Python Engineer", 
            "FastAPI", 
            "AI Engineer", 
            "Desenvolvedor Python", 
            "Engenheiro de IA", 
            "RAG Developer"
        ]
        
        # Chaves de API vindas do seu .env
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID")
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY")
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")  # Usando o nome exato do seu .env
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_gupy_jobs(self) -> List[Dict]:
        """
        Busca vagas via API pública do portal da Gupy (Filtro: Remoto + Termos).
        """
        jobs = []
        termos = ["Python", "IA", "FastAPI", "Artificial Intelligence", "Backend"]
        
        for termo in termos:
            # Query otimizada enviando workplaceType=remote
            url = f"https://portal.api.gupy.io/api/v1/jobs?name={termo}&workplaceType=remote&limit=15"
            try:
                res = requests.get(url, headers=self.headers, timeout=10)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    for item in data:
                        job_id = f"gupy_{item.get('id')}"
                        jobs.append({
                            'id': job_id,
                            'titulo': item.get('name'),
                            'empresa': item.get('companyName', 'Empresa parceira Gupy'),
                            'modelo': '100% Remoto',
                            'descricao': item.get('description') or f"Vaga de {item.get('name')} publicada via Portal Gupy.",
                            'url': item.get('jobUrl'),
                            'fonte': 'Gupy Portal'
                        })
            except Exception as e:
                print(f"❌ Erro ao buscar na Gupy para '{termo}': {e}")
                
        return jobs

    def fetch_remotar_jobs(self) -> List[Dict]:
        """
        Scraping na plataforma Remotar.com.br.
        """
        if not BeautifulSoup:
            print("⚠️ BeautifulSoup (bs4) não disponível. Pulando scraping da Remotar.")
            return []

        jobs = []
        # URL de busca focada em vagas de programação/tecnologia
        url = "https://remotar.com.br/vagas?q=python"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Procura por links ou cards de vagas na estrutura do site
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    # Filtra apenas links direcionados para páginas de vagas
                    if '/vaga/' in href or '/job/' in href:
                        titulo = a_tag.get_text(strip=True)
                        
                        # Filtra apenas títulos relevantes do seu interesse
                        if any(k.lower() in titulo.lower() for k in ['python', 'backend', 'ia', 'ai', 'developer', 'engenheiro']):
                            full_url = href if href.startswith('http') else f"https://remotar.com.br{href}"
                            job_id = f"remotar_{abs(hash(full_url))}"
                            
                            jobs.append({
                                'id': job_id,
                                'titulo': titulo[:80],
                                'empresa': 'Remotar Partner',
                                'modelo': '100% Remoto',
                                'descricao': f"Vaga 100% remota capturada via Remotar.com.br: {titulo}",
                                'url': full_url,
                                'fonte': 'Remotar.com.br'
                            })
        except Exception as e:
            print(f"❌ Erro no scraping da Remotar: {e}")

        return jobs

    def fetch_adzuna_jobs(self) -> List[Dict]:
        """Busca granular na Adzuna por país e lista de palavras-chave."""
        jobs = []
        if not self.adzuna_app_id or not self.adzuna_app_key:
            print("⚠️ ADZUNA_APP_ID ou ADZUNA_APP_KEY ausentes no .env.")
            return jobs

        paises = ['br', 'us']
        for pais in paises:
            base_url = f"https://api.adzuna.com/v1/api/jobs/{pais}/search/1"
            
            for keyword in self.keywords:
                params = {
                    'app_id': self.adzuna_app_id,
                    'app_key': self.adzuna_app_key,
                    'results_per_page': 5,
                    'what': f"{keyword} remote",
                    'content-type': 'application/json'
                }

                try:
                    response = requests.get(base_url, params=params, timeout=10)
                    if response.status_code == 200:
                        for item in response.json().get('results', []):
                            jobs.append({
                                'id': f"adzuna_{item.get('id')}",
                                'titulo': item.get('title'),
                                'empresa': item.get('company', {}).get('display_name', 'Empresa Não Informada'),
                                'modelo': 'Remoto',
                                'descricao': item.get('description'),
                                'url': item.get('redirect_url'),
                                'fonte': f'Adzuna ({pais.upper()})'
                            })
                except Exception as e:
                    print(f"❌ Erro na Adzuna [{pais.upper()}] para '{keyword}': {e}")

        return jobs

    def fetch_serpapi_google_jobs(self) -> List[Dict]:
        """Busca no Google Jobs via SerpApi."""
        if not self.serpapi_key:
            print("⚠️ SERPAPI_API_KEY ausente no .env. Pulando Google Jobs.")
            return []

        jobs = []
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_jobs",
            "q": "(Python OR 'AI Engineer' OR FastAPI) remoto",
            "hl": "pt",
            "gl": "br",
            "api_key": self.serpapi_key
        }

        try:
            res = requests.get(url, params=params, timeout=20)
            if res.status_code == 200:
                for item in res.json().get("jobs_results", []):
                    apply_link = "#"
                    if item.get("apply_options"):
                        apply_link = item["apply_options"][0].get("link", "#")
                    elif item.get("share_link"):
                        apply_link = item.get("share_link")

                    jobs.append({
                        'id': f"google_{item.get('job_id')}",
                        'titulo': item.get('title'),
                        'empresa': item.get('company_name', 'Empresa Não Informada'),
                        'modelo': 'Remoto',
                        'descricao': item.get('description', ''),
                        'url': apply_link,
                        'fonte': 'Google Jobs (SerpApi)'
                    })
        except Exception as e:
            print(f"❌ Erro no Google Jobs (SerpApi): {e}")

        return jobs

    def fetch_mock_jobs(self) -> List[Dict]:
        return [
            {
                'id': 'mock_001',
                'titulo': 'Engenheiro de IA & Backend Python Sênior',
                'empresa': 'HealthTech Global',
                'modelo': '100% Remoto',
                'descricao': 'Vaga remota Python, FastAPI, PostgreSQL, pgvector e pipelines RAG.',
                'url': 'https://exemplo.com/vaga/123',
                'fonte': 'Mock Teste'
            }
        ]

    def get_all_jobs(self) -> List[Dict]:
        print("🌐 Iniciando coleta MULTI-FONTE de vagas...")
        all_jobs = []

        # Executa todas as fontes
        all_jobs.extend(self.fetch_gupy_jobs())
        all_jobs.extend(self.fetch_remotar_jobs())
        all_jobs.extend(self.fetch_adzuna_jobs())
        all_jobs.extend(self.fetch_serpapi_google_jobs())

        # Deduplicação interna por ID
        vagas_unicas = {job['id']: job for job in all_jobs}
        resultado = list(vagas_unicas.values())

        if not resultado:
            print("ℹ️ Nenhuma API/Scraper retornou vagas. Carregando MOCK...")
            resultado = self.fetch_mock_jobs()

        print(f"📊 Total de vagas únicas coletadas nesta rodada: {len(resultado)}")
        return resultado


if __name__ == "__main__":
    fetcher = JobFetcher()
    vagas = fetcher.get_all_jobs()
    for v in vagas[:10]:
        print(f"[{v['fonte']}] {v['titulo']} - {v['empresa']}")