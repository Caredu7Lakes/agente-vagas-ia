"""Escreve o resumo da execução no painel do GitHub Actions.

Sem isso, a única forma de saber o que o agente fez é abrir centenas de linhas
de log. Com isso, o card do run responde sozinho.
"""

import os
from collections import Counter


def publicar_resumo(titulo: str, metricas: dict, motivos: Counter | None = None) -> None:
    """Publica em $GITHUB_STEP_SUMMARY. No-op fora do CI."""
    caminho = os.getenv("GITHUB_STEP_SUMMARY")
    if not caminho:
        return

    linhas = [f"## {titulo}", "", "| Métrica | Valor |", "| --- | --- |"]
    linhas += [f"| {k} | {v} |" for k, v in metricas.items()]

    if motivos:
        linhas += ["", "### Motivos de rejeição", "", "| Motivo | Ocorrências |", "| --- | --- |"]
        linhas += [f"| {m} | {n} |" for m, n in motivos.most_common()]

    with open(caminho, "a", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n\n")