from src.agents.applicant_agent import ApplicantAgent
from src.services.email_service import EmailReaderService
from src.services.notify_service import NotifyService

BLOQUEIO_GEO = (
    "must be based in the us",
    "us citizens only",
    "green card",
    "authorized to work in the united states",
    "eligible to work in the us",
    "work authorization in the us",
    "w2 only",
    "no c2c",
    "usc only",
)


def restricao_geografica(texto: str) -> bool:
    t = texto.lower()
    return any(termo in t for termo in BLOQUEIO_GEO)

def run_applicant_pipeline():
    print("🤖 [Agente Candidato Multi-Trilha] Iniciando ciclo de triagem...")

    email_service = EmailReaderService()
    notify_service = NotifyService()
    agent = ApplicantAgent()

    # 1. Leitura de e-mails não lidos contendo palavras-chave relevantes
    vagas_encontradas = email_service.fetch_unread_job_emails(search_keyword="vaga")

    total_encontradas = len(vagas_encontradas)
    total_descartadas = 0
    enviados_eng_ia = 0
    enviados_backend = 0

    if total_encontradas == 0:
        print("ℹ️ Nenhum novo alerta de vaga não lido na caixa de entrada.")
        return

    # 2. Processamento Inteligente
    for item in vagas_encontradas:
        print(f"\n🔍 Analisando e-mail: '{item['subject']}'...")

        if restricao_geografica(f"{item['subject']} {item['body']}"):
            total_descartadas += 1
            print("🚫 VAGA DESCARTADA | Motivo: restrição geográfica (exige autorização de trabalho nos EUA)")
            continue    

        avaliacao = agent.evaluate_email_job(
            email_subject=item["subject"],
            email_body=item["body"]
        )

        if avaliacao["aprovado"]:
            trilha = avaliacao["trilha"]
            cv_especifico = avaliacao["cv_path"]

            print(f"✅ VAGA APROVADA | Trilha: [{trilha}] | Cargo: {avaliacao['cargo']} | Match: {avaliacao['score']}%")
            print(f"📄 Selecionado anexo: {cv_especifico}")

            # Gerar Carta de Apresentação Adaptada
            cover_letter = agent.generate_cover_letter(
                cargo=avaliacao["cargo"],
                trilha=trilha,
                resumo_vaga=avaliacao["resumo"]
            )

            assunto_email = f"Candidatura: {avaliacao['cargo']}"

            # Enviar e-mail anexando O CURRÍCULO CORRETO para a trilha
            sucesso = email_service.send_application_email(
                to_email=avaliacao["email_destino"],
                subject=assunto_email,
                cover_letter=cover_letter,
                cv_path=cv_especifico
            )

            if sucesso:
                if trilha == "ENG_IA":
                    enviados_eng_ia += 1
                else:
                    enviados_backend += 1

            notify_service.send_notification(
                title=f"Candidatura: {avaliacao['cargo']}",
                message=(
                    f"Trilha: {trilha}\n"
                    f"Match: {avaliacao['score']}%\n"
                    f"Destino: {avaliacao['email_destino']}"
                ),
            )
        else:
            total_descartadas += 1
            print(f"🚫 VAGA DESCARTADA | Motivo: {avaliacao['motivo']}")

    # 3. Métricas Detalhadas do Funil
    total_enviadas = enviados_eng_ia + enviados_backend
    taxa_conversao = (total_enviadas / total_encontradas * 100) if total_encontradas > 0 else 0

    print("\n" + "=" * 55)
    print("📊 FUNIL DE EFICIÊNCIA MULTI-TRILHA (IA vs BACKEND)")
    print("=" * 55)
    print(f"📥 Total de Vagas Encontradas      : {total_encontradas}")
    print(f"🚫 Vagas Descartadas               : {total_descartadas}")
    print(f"🎯 Enviadas para Engenharia de IA  : {enviados_eng_ia} (CV: curriculo_eng.docx)")
    print(f"🎯 Enviadas para Backend Python    : {enviados_backend} (CV: curriculo_back.docx)")
    print(f"🚀 Total de Candidaturas Enviadas  : {total_enviadas}")
    print(f"📈 Taxa de Conversão do Funil      : {taxa_conversao:.1f}%")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    run_applicant_pipeline()