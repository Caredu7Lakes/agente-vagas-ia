🤖 Job Hunter AI Agent
Um Agente de IA Autônomo projetado para automatizar a busca, avaliação e notificação de vagas de emprego de alta relevância (foco em desenvolvimento Python, FastAPI, Engenharia de IA e RAG).

O sistema agrega vagas de múltiplas fontes, utiliza modelos de linguagem da OpenAI (GPT-4o-mini) para realizar o match cultural e técnico baseado no currículo do candidato, mantém o histórico em banco de dados para evitar duplicatas e envia alertas formatados por e-mail em tempo real.

🛠️ Arquitetura e Módulos do Sistema
  ┌─────────────────────────────────────────────────────────────┐
  │                       JobHunterAgent                        │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
  │ JobFetcher   │        │ JobEvaluator │        │ Notification │
  │ (Scrapers &  │ ──────►│ (OpenAI GPT  │ ──────►│   Service    │
  │     APIs)    │        │  Evaluator)  │        │ (iCloud Mail)│
  └──────────────┘        └──────────────┘        └──────────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
             ┌──────────────┐
             │ SQLite DB    │
             │(vagas.db)    │
             └──────────────┘
1. 🌐 Multi-Source Job Fetcher (src/fetcher.py)
Coleta vagas em tempo real utilizando estratégia híbrida de APIs Oficiais e Web Scraping:

Adzuna API: Coleta de oportunidades nacionais e internacionais (BR/US).

SerpApi (Google Jobs): Agregação de portais globais como LinkedIn, Glassdoor, Catho e Indeed.

Gupy Portal API: Consumo da API pública de vagas do ecossistema Gupy.

Remotar Scraper: Extração de oportunidades 100% remotas no mercado brasileiro.

2. 🧠 Evaluator de Match com IA (src/evaluator.py)
Processa o payload de cada vaga utilizando o modelo gpt-4o-mini.

Compara requisitos de stack, senioridade e modelo de trabalho (100% Remoto estrito) contra os critérios do currículo do candidato.

Retorna estruturado em JSON com pontuação de Match (Score de 0 a 100%) e justificativa técnica da decisão.

3. 💾 Deduplicação & Persistência (src/database.py)
Utiliza SQLite (vagas.db) para registro de histórico permanente.

Verifica duplicatas tanto por ID de origem quanto por URL normalizada, evitando chamadas redundantes à API da OpenAI e notificações repetidas.

4. 📬 Serviço de Notificação (src/notifier.py)
Envia relatórios formatados em HTML/Texto contendo título da vaga, empresa, resumo da análise da IA, nota de compatibilidade e link direto para candidatura.

🚀 Tecnologias Utilizadas
Linguagem: Python 3.12+

Inteligência Artificial: OpenAI API (gpt-4o-mini)

APIs & Scraping: requests, beautifulsoup4, python-dotenv

Banco de Dados: SQLite3

Ambiente Virtual: venv

⚙️ Como Executar o Projeto
1. Clonar o Repositório
git clone https://github.com/SEU_USUARIO/agente-vagas-ia.git
cd agente-vagas-ia

2. Configurar o Ambiente Virtual
Windows: python -m venv venv e depois venv\Scripts\activate

Linux/Mac: python3 -m venv venv e depois source venv/bin/activate

3. Instalar Dependências
pip install -r requirements.txt

4. Configurar Variáveis de Ambiente (.env)
Crie um arquivo .env na raiz do projeto contendo:

OPENAI_API_KEY="sua-chave-openai"

EMAIL_SENDER="seu_email@icloud.com"

EMAIL_PASSWORD="sua-senha-de-app-icloud"

EMAIL_RECEIVER="seu_email@icloud.com"

ADZUNA_APP_ID="seu-app-id-adzuna"

ADZUNA_APP_KEY="sua-key-adzuna"

SERPAPI_API_KEY="sua-chave-serpapi"

5. Executar o Agente
python main.py

## Currículos no CI (base64-encoded secrets)

Os arquivos `assets/curriculo_*.docx` **não são versionados** (contêm dados
pessoais). Para que o agente possa anexá-los no GitHub Actions, eles são
armazenados como secrets codificados em base64 e restaurados em disco no
início do workflow.

### Regerar os secrets

Necessário sempre que um currículo for alterado — o secret é um snapshot
congelado e não avisa quando fica desatualizado.

**PowerShell (Windows):**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("assets\curriculo_back.docx")) | Set-Clipboard
```
Colar em Settings > Secrets and variables > Actions > New repository secret.

| Arquivo                      | Secret        |
|------------------------------|---------------|
| `assets/curriculo_back.docx` | `CV_BACK_B64` |
| `assets/curriculo_eng.docx`  | `CV_ENG_B64`  |

**Com GitHub CLI:**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("assets\curriculo_back.docx")) | gh secret set CV_BACK_B64
```

**Bash/Linux/macOS:**
```bash
base64 -w0 assets/curriculo_back.docx | gh secret set CV_BACK_B64
```

### Restrições

- Limite de 64 KB por secret. Base64 infla ~33%, então o `.docx` original
  deve ficar abaixo de ~48 KB. Atual: 13 KB.
- Não usar `>` no PowerShell para salvar o base64 em arquivo — a saída sai
  em UTF-16 e corrompe o conteúdo. Use `Set-Clipboard` ou pipe direto.
- O step `Restaurar currículos` roda `file` nos arquivos decodificados para
  validar a integridade antes da execução do agente.

📌 Licença
Este projeto é de uso pessoal e educacional sob a licença MIT.