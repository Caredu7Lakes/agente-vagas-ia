import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class ApplicantAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.blacklist_words = ["encerrada", "fechada", "newsletter", "no-reply", "noreply", "descadastrar"]
        
        # Mapeamento dos currículos específicos
        self.cv_paths = {
            "ENG_IA": os.path.join("assets", "curriculo_eng.docx"),
            "BACKEND_PYTHON": os.path.join("assets", "curriculo_back.docx")
}
        

    def evaluate_email_job(self, email_subject: str, email_body: str) -> dict:
        """
        Avalia a vaga, classifica a trilha (Engenharia IA vs Backend Python) 
        e define o currículo correto a ser enviado.
        """
        texto_completo = f"{email_subject} {email_body}".lower()
        
        # 1. Filtro de Bloqueio por Blacklist
        for palavra in self.blacklist_words:
            if palavra in texto_completo:
                return {
                    "aprovado": False,
                    "email_destino": None,
                    "motivo": f"Contém palavra-chave de bloqueio: '{palavra}'"
                }

        # 2. Análise Estruturada via GPT-4o-mini
        prompt = f"""
        Você é um auditor de candidaturas de tecnologia especializado em duas frentes:
        FRENTE A: Engenheiro de Inteligência Artificial Júnior / Machine Learning / LLM
        FRENTE B: Desenvolvedor Back-end Python Júnior/Pleno (APIs, Django, FastAPI, Flask, SQL)

        Analise o e-mail de vaga abaixo:
        ASSUNTO: {email_subject}
        CORPO:
        {email_body}

        REGRAS DE VALIDAÇÃO:
        1. Identifique se existe um e-mail VÁLIDO de recrutador/empresa (ignorar no-reply/automáticos).
        2. Avalie a senioridade: Aprovado se for Estágio, Júnior, Pleno ou Assistente. Reprovado se for Sênior, Specialist, Lead ou Diretor.
        3. Classifique a TRILHA da vaga EXATAMENTE como 'ENG_IA' ou 'BACKEND_PYTHON' (Se não se enquadrar em nenhuma das duas, marque 'OUTRA').
        4. Calcule o Score de aderência de 0 a 100%.

        Responda EXATAMENTE em formato JSON:
        {{
            "has_direct_email": true/false,
            "target_email": "string ou null",
            "cargo_identificado": "string",
            "trilha": "ENG_IA" | "BACKEND_PYTHON" | "OUTRA",
            "score_aderencia": integer,
            "senioridade_incompativel": true/false,
            "resumo_vaga": "string curto"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            dados = json.loads(response.choices[0].message.content)

            has_email = dados.get("has_direct_email", False) and bool(dados.get("target_email"))
            score_ok = dados.get("score_aderencia", 0) >= 70
            senioridade_ok = not dados.get("senioridade_incompativel", True)
            trilha_valida = dados.get("trilha") in ["ENG_IA", "BACKEND_PYTHON"]

            if has_email and score_ok and senioridade_ok and trilha_valida:
                trilha_escolhida = dados["trilha"]
                return {
                    "aprovado": True,
                    "email_destino": dados["target_email"],
                    "cargo": dados["cargo_identificado"],
                    "trilha": trilha_escolhida,
                    "cv_path": self.cv_paths[trilha_escolhida], # Seleciona o CV específico
                    "score": dados["score_aderencia"],
                    "resumo": dados["resumo_vaga"],
                    "motivo": None
                }
            else:
                motivos = []
                if not has_email: motivos.append("Sem e-mail direto de contato")
                if not score_ok: motivos.append(f"Score baixo ({dados.get('score_aderencia')}%)")
                if not senioridade_ok: motivos.append("Senioridade incompatível")
                if not trilha_valida: motivos.append(f"Fora dos escopos-alvo (Trilha: {dados.get('trilha')})")

                return {
                    "aprovado": False,
                    "email_destino": None,
                    "motivo": " | ".join(motivos)
                }

        except Exception as e:
            return {
                "aprovado": False,
                "email_destino": None,
                "motivo": f"Erro no processamento da IA: {e}"
            }

    def generate_cover_letter(self, cargo: str, trilha: str, resumo_vaga: str) -> str:
        """Gera uma Cover Letter focada no nicho da vaga (Engenharia IA ou Python)."""
        foco_perfil = (
            "Engenharia de IA, LLMs, consumo de APIs de IA e automação inteligente"
            if trilha == "ENG_IA"
            else "Desenvolvimento Back-end em Python, criação de APIs RESTful, SQL e arquitetura limpa"
        )

        prompt = f"""
        Escreva um e-mail de apresentação (Cover Letter) profissional, formal e direto para a vaga de '{cargo}'.
        Resumo da oportunidade: {resumo_vaga}.
        
        Orientações:
        - Destaque meu foco técnico em: {foco_perfil}.
        - Deixe claro que o meu Currículo especializado em formato PDF está em anexo.
        - Mantenha o texto objetivo com 2 a 3 parágrafos curtos.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content