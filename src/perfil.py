"""Fonte única de verdade sobre o perfil do candidato e os critérios de aceite.

Este módulo existe porque `evaluator.py` (agente de busca) e `agents/applicant_agent.py`
(agente candidato) avaliam a mesma coisa em momentos diferentes do pipeline. Manter os
critérios duplicados fez os dois divergirem: um descrevia o candidato como Sênior/Lead e
o outro como Júnior/Pleno, permitindo que vagas SR passassem pelo primeiro filtro.

Qualquer regra nova de aceite entra AQUI, nunca direto num dos prompts.
"""

import re

SCORE_MINIMO = 70

PERFIL_CANDIDATO = """
CANDIDATO: CARLOS EDUARDO DOS SANTOS FILHO
- Perfil: Engenheiro de IA Júnior | Desenvolvedor Backend Python Júnior | QA de Automação
- Modelo Obrigatório: 100% Remoto (Home Office)
- Senioridade-alvo: Estágio, Trainee, Júnior, Assistente ou Pleno inicial
- Localização: Brasil (Itatiba/SP). SEM autorização de trabalho nos EUA ou União Europeia.
- Requisitos Principais: Python, FastAPI, SQLAlchemy, PostgreSQL, RAG, pgvector, FAISS,
  Docker, pytest, APIs LLM (OpenAI/Anthropic).
- Diferenciais: HealthTech / Biotecnologia, CI/CD, AWS, arquiteturas de agentes.
"""

REGRAS_COMUNS = """
1. MODELO: Se a vaga não for 100% remota, rejeite.
2. SENIORIDADE: Aceite apenas Estágio, Trainee, Júnior, Assistente ou Pleno.
   REJEITE Sênior, Sr., Specialist, Lead, Staff, Principal, Head, Diretor, Manager,
   Arquiteto e Especialista — inclusive quando o título usar abreviações (SR, SR.).
3. GEOGRAFIA: O candidato reside no Brasil e não possui autorização de trabalho nos
   EUA ou União Europeia. Rejeite vagas que exijam residência, presença física ou
   work authorization fora do Brasil. Vagas remotas que aceitam contratação
   internacional (PJ/contractor) são aceitáveis.
4. ESCOPO: A vaga deve envolver Python e/ou o ecossistema de Engenharia de IA / Backend.
"""

# Guard determinístico: barra antes de gastar token com a LLM.
# Fronteiras de palavra evitam falso positivo (ex.: "SR" dentro de outra palavra).
_PADRAO_SENIORIDADE_BLOQUEADA = re.compile(
    r"\b("
    r"s[êe]nior|sr\.?|specialist|especialista|"
    r"lead|tech\s*lead|staff|principal|"
    r"head|diretor|director|manager|gerente|"
    r"arquiteto|architect|coordenador|"
    r"distinguished|expert|iii|iv"
    r")\b",
    re.IGNORECASE,
)

_PADRAO_RESTRICAO_GEOGRAFICA = re.compile(
    r"("
    r"must be based in the us|us citizens? only|green card|"
    r"authorized to work in the united states|eligible to work in the us|"
    r"work authorization in the us|w2 only|no c2c|usc only|"
    r"eu work permit|right to work in the uk"
    r")",
    re.IGNORECASE,
)


def senioridade_bloqueada(texto: str) -> str | None:
    """Retorna o termo de senioridade incompatível encontrado, ou None."""
    achado = _PADRAO_SENIORIDADE_BLOQUEADA.search(texto or "")
    return achado.group(0) if achado else None


def restricao_geografica(texto: str) -> str | None:
    """Retorna o termo de restrição geográfica encontrado, ou None."""
    achado = _PADRAO_RESTRICAO_GEOGRAFICA.search(texto or "")
    return achado.group(0) if achado else None