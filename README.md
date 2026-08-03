# agente-vagas-ia

Agente autônomo de busca e candidatura a vagas, executado de forma agendada via GitHub Actions.

Arquitetura de **dois agentes** que se comunicam por e-mail:

- **Agente de Busca** (`src/main.py`) — coleta vagas em Adzuna e SerpAPI, avalia aderência
  com GPT-4o-mini, deduplica contra o histórico local e notifica por e-mail.
- **Agente Candidato** (`src/main_applicant.py`) — lê a caixa de entrada, reavalia cada
  vaga, seleciona a trilha (Engenharia de IA ou Backend Python), gera carta de apresentação
  adaptada e dispara a candidatura com o currículo correspondente anexado.

Notificação push a cada candidatura enviada, via ntfy.sh.

---

## Stack

Python 3.12 · OpenAI API · SQLite · IMAP/SMTP · GitHub Actions · ntfy.sh

---

## Estrutura

```
src/
├── config.py                    # Settings centralizado + validação de ambiente
├── main.py                      # Entrypoint do agente de busca
├── main_applicant.py            # Entrypoint do agente candidato
├── fetcher.py                   # Coleta em Adzuna / SerpAPI
├── evaluator.py                 # Scoring de aderência
├── database.py                  # Persistência e deduplicação (SQLite)
├── notifier.py                  # Notificação por e-mail
├── agents/
│   └── applicant_agent.py       # Avaliação de vaga e geração de carta
└── services/
    ├── email_service.py         # IMAP (leitura) e SMTP (envio com anexo)
    └── notify_service.py        # Push via ntfy.sh
```

---

## Setup local

```bash
pip install -r requirements.txt
cp .env.example .env    # preencher as variáveis
python -m src.main
python -m src.main_applicant
```

> Executar com `python -m` (não `python src/main.py`) — os módulos usam imports
> absolutos a partir da raiz do pacote.

### Variáveis de ambiente

Todas as variáveis são declaradas em `.env.example` e resolvidas por `src/config.py`.
`Settings.validar()` roda no início de cada pipeline e falha imediatamente listando o
que estiver ausente.

| Grupo | Variáveis |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| E-mail | `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_RECEIVER`, `EMAIL_IMAP_SERVER`, `EMAIL_SMTP_SERVER`, `EMAIL_SMTP_PORT` |
| Fontes de vagas | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `SERPAPI_API_KEY` |
| Notificação | `NTFY_TOPIC` |

O `.env` está no `.gitignore` e nunca deve ser versionado.

---

## Execução automatizada (CI)

O workflow `.github/workflows/agente.yml` roda **de segunda a sexta, às 08:00 e 17:00 BRT**
(`cron: '0 11,20 * * 1-5'`, em UTC), e também sob demanda via **Actions → Run workflow**.

Contenções de falha configuradas:

- `timeout-minutes: 20` — teto de execução do job.
- `concurrency` com `cancel-in-progress` — impede runs sobrepostos disputando o IMAP.
- Step `Validar secrets` — falha em ~1 s se faltar configuração, antes de qualquer rede.
- `if: always()` na persistência do banco — preserva a deduplicação mesmo em falha.

> Workflows agendados são desativados automaticamente após 60 dias sem atividade no
> repositório. O GitHub notifica por e-mail antes.

---

## Notificação push (ntfy.sh)

1. Gerar um tópico aleatório:
   ```powershell
   python -c "import secrets; print('vagas-' + secrets.token_urlsafe(16))"
   ```
2. Definir como `NTFY_TOPIC` no `.env` e nos GitHub Secrets.
3. Instalar o app [ntfy](https://ntfy.sh) e inscrever-se abrindo `https://ntfy.sh/<TOPICO>`
   no navegador do celular — evita erro de digitação com caracteres ambíguos (`l`, `I`, `1`).

**O nome do tópico é a credencial.** Qualquer pessoa que o conheça consegue ler as
notificações. Trate-o como senha.

---

## Currículos no CI (base64-encoded secrets)

Os arquivos `assets/curriculo_*.docx` **não são versionados** — contêm dados pessoais.
Para que o agente possa anexá-los no GitHub Actions, são armazenados como secrets
codificados em base64 e restaurados em disco no início do workflow.

### Regerar os secrets

Necessário sempre que um currículo for alterado — o secret é um snapshot congelado e
não avisa quando fica desatualizado.

**PowerShell (Windows):**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("assets\curriculo_back.docx")) | Set-Clipboard
```
Colar em Settings → Secrets and variables → Actions → New repository secret.

| Arquivo | Secret |
|---|---|
| `assets/curriculo_back.docx` | `CV_BACK_B64` |
| `assets/curriculo_eng.docx` | `CV_ENG_B64` |

**Com GitHub CLI:**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("assets\curriculo_back.docx")) | gh secret set CV_BACK_B64
```

**Bash:**
```bash
base64 -w0 assets/curriculo_back.docx | gh secret set CV_BACK_B64
```

### Restrições

- Limite de 64 KB por secret. Base64 infla ~33%, então o `.docx` original deve ficar
  abaixo de ~48 KB. Atual: 13 KB.
- Não usar `>` no PowerShell para salvar o base64 em arquivo — a saída sai em UTF-16 e
  corrompe o conteúdo. Usar `Set-Clipboard` ou pipe direto.
- O step `Restaurar currículos` roda `file` nos arquivos decodificados para validar a
  integridade antes da execução do agente.

---

## Monitoramento

```powershell
gh run list --workflow=agente.yml --limit 10
gh run view <RUN_ID> --log-failed
gh run watch <RUN_ID>
```

---

## Limitações conhecidas

- Os dois agentes rodam sequencialmente no mesmo job. Se o e-mail do agente de busca não
  chegar ao IMAP a tempo, o agente candidato reporta caixa vazia. Mitigação prevista:
  cron separado com defasagem.
- Runs agendados podem atrasar em horários de pico do GitHub Actions.
- `vagas.db` é versionado em Git. Como SQLite é binário, cada commit guarda o arquivo
  inteiro; se crescer demais, migrar para branch órfã de dados.

---

## Licença

MIT