import json
import os

from openai import OpenAI

from src.perfil import (
    PERFIL_CANDIDATO,
    REGRAS_COMUNS,
    restricao_geografica,
    senioridade_bloqueada,
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def avaliar_vaga(titulo_vaga: str, descricao_vaga: str) -> dict:
    """Avalia a aderência da vaga ao perfil do candidato usando GPT-4o-mini.

    Antes de chamar a LLM, aplica guards determinísticos de senioridade e geografia.
    Isso barra os casos óbvios sem custo de token e sem depender do julgamento do modelo.
    """
    texto_completo = f"{titulo_vaga} {descricao_vaga}"

    termo_senioridade = senioridade_bloqueada(titulo_vaga)
    if termo_senioridade:
        return {
            "match": False,
            "score": 0,
            "motivo_rejeicao": f"Senioridade incompatível no título: '{termo_senioridade}'",
            "resumo": titulo_vaga,
            "pontos_fortes": [],
        }

    termo_geo = restricao_geografica(texto_completo)
    if termo_geo:
        return {
            "match": False,
            "score": 0,
            "motivo_rejeicao": f"Restrição geográfica: '{termo_geo}'",
            "resumo": titulo_vaga,
            "pontos_fortes": [],
        }

    prompt = f"""
    Você é um Tech Lead e Recrutador Sênior avaliando uma oportunidade de emprego.

    CRITÉRIOS E PERFIL DO CANDIDATO:
    {PERFIL_CANDIDATO}

    DADOS DA VAGA:
    Título: {titulo_vaga}
    Descrição: {descricao_vaga}

    REGRAS DE DECISÃO (qualquer violação implica "match": false):
    {REGRAS_COMUNS}

    Responda EXCLUSIVAMENTE em formato JSON estrito com a seguinte estrutura:
    {{
        "match": true ou false,
        "score": número de 0 a 100,
        "senioridade_detectada": "string",
        "localizacao": "string ou null",
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
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ Erro ao chamar API da OpenAI no evaluator: {type(e).__name__}: {e}")
        return {
            "match": False,
            "score": 0,
            "motivo_rejeicao": f"Erro no processamento da IA: {e}",
            "resumo": "Falha na avaliação.",
            "pontos_fortes": [],
        }