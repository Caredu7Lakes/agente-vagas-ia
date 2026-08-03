"""Testes dos guards determinísticos de aceite.

Estes testes existem porque a regressão que motivou o refactor — vagas Sênior passando
pelo agente de busca — não era detectável por lint nem por leitura de log. Score alto
não é sinal de acerto: é apenas um número que a LLM produziu.
"""

import pytest

from src.perfil import restricao_geografica, senioridade_bloqueada


@pytest.mark.parametrize(
    "titulo",
    [
        "ENGENHEIRO DE IA SR - REMOTO",
        "Engenheiro de IA Sênior",
        "Senior Python Developer",
        "Sr. Backend Engineer",
        "Tech Lead - Machine Learning",
        "Staff AI Engineer",
        "Principal Software Engineer",
        "Especialista em Dados",
        "Arquiteto de Soluções",
        "Head of Engineering",
        "Distinguished AI Engineer",  # regressão real observada em 03/08/2026
    ],
)
def test_senioridade_incompativel_e_bloqueada(titulo):
    assert senioridade_bloqueada(titulo) is not None, f"deveria bloquear: {titulo}"


@pytest.mark.parametrize(
    "titulo",
    [
        "Desenvolvedor Python Júnior",
        "Estágio em Engenharia de IA",
        "Backend Developer Jr",
        "Analista de Dados Pleno",
        "Trainee de Desenvolvimento",
        "Assistente de TI",
    ],
)
def test_senioridade_alvo_e_aceita(titulo):
    assert senioridade_bloqueada(titulo) is None, f"não deveria bloquear: {titulo}"


@pytest.mark.parametrize(
    "descricao",
    [
        "Candidates must be based in the US.",
        "US citizens only, no sponsorship available.",
        "Requires green card or equivalent.",
        "Must be authorized to work in the United States.",
        "W2 only, no C2C.",
    ],
)
def test_restricao_geografica_e_detectada(descricao):
    assert restricao_geografica(descricao) is not None, f"deveria bloquear: {descricao}"


@pytest.mark.parametrize(
    "descricao",
    [
        "Vaga 100% remota, contratação PJ, aceita candidatos do Brasil.",
        "Remote position open to contractors worldwide.",
        "Trabalho remoto para toda a América Latina.",
    ],
)
def test_vaga_remota_internacional_e_aceita(descricao):
    assert restricao_geografica(descricao) is None, f"não deveria bloquear: {descricao}"


def test_entrada_vazia_nao_quebra():
    assert senioridade_bloqueada("") is None
    assert senioridade_bloqueada(None) is None
    assert restricao_geografica("") is None