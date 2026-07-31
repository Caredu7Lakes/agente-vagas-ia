import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Inicializa o cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MEUS_CRITERIOS = """
CANDIDATO: CARLOS EDUARDO DOS SANTOS FILHO
- Perfil: Engenheiro de IA | Desenvolvedor Backend Python | QA de Automação
- Modelo Obrigatório: 100% Remoto (Home Office)
- Senioridade: Pleno, Sênior, Mid-Level ou Lead
- Pretensão Salarial: A negociar / Compatível
- Requisitos Principais: Python, FastAPI, SQLAlchemy, PostgreSQL, RAG, pgvector, FAISS, Docker, pytest, APIs LLM (OpenAI/Anthropic).
- Diferenciais: Conhecimento em HealthTech / Biotecnologia, CI/CD, AWS e arquiteturas de agentes.
"""

def avaliar_vaga(titulo_vaga: str, descricao_vaga: str) -> dict:
    """
    Avalia a aderência da vaga com o perfil do candidato usando GPT-4o-mini.
    """
    prompt = f"""
    Você é um Tech Lead e Recrutador Sênior avaliando uma oportunidade de emprego.

    CRITÉRIOS E PERFIL DO CANDIDATO:
    {MEUS_CRITERIOS}

    DADOS DA VAGA:
    Título: {titulo_vaga}
    Descrição: {descricao_vaga}

    REGRAS DE DECISÃO:
    1. Se o modelo de trabalho NÃO for 100% Remoto, defina "match": false.
    2. A vaga deve envolver Python e/ou ecossistema de Engenharia de IA / Backend.

    Responda EXCLUSIVAMENTE em formato JSON estrito com a seguinte estrutura:
    {{
        "match": true ou false,
        "score": número de 0 a 100,
        "motivo_rejeicao": "Explicação em 1 frase se match=false ou string vazia",
        "resumo": "Resumo executivo da vaga em 2 frases",
        "pontos_fortes": ["Lista com 2 a 3 pontos que combinam com o currículo"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Erro ao chamar API da OpenAI no evaluator: {e}")
        return {
            "match": False,
            "score": 0,
            "motivo_rejeicao": f"Erro no processamento da IA: {e}",
            "resumo": "Falha na avaliação.",
            "pontos_fortes": []
        }