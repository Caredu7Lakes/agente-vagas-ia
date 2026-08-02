import time
from datetime import datetime
from dotenv import load_dotenv

# Importação dos módulos criados na pasta src/
from src.fetcher import JobFetcher
from src.database import Database
from src.evaluator import avaliar_vaga  # Função de avaliação com a IA (OpenAI)
from src.notifier import enviar_email_vaga

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

INTERVALO_HORAS = 1
INTERVALO_SEGUNDOS = INTERVALO_HORAS * 3600

def executar_ciclo_agente():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"\n==================================================")
    print(f"🤖 [AGENTE IA] Iniciando ciclo de busca: {agora}")
    print(f"==================================================")

    # 1. Inicializa o banco de dados e o coletor de vagas
    db = Database()
    fetcher = JobFetcher()

    try:
        # 2. Coleta vagas da internet/APIs
        vagas_coletadas = fetcher.get_all_jobs()
        print(f"📥 Vagas retornadas pelas fontes: {len(vagas_coletadas)}")

        novas_vagas_processadas = 0

        for vaga in vagas_coletadas:
            vaga_id = vaga["id"]

            # 3. Verifica se a vaga já foi analisada antes (Deduplicação)
            if db.vaga_ja_processada(vaga_id, url=vaga.get("url")):
                print(f"⏭️ Pulando vaga '{vaga['titulo']}' (Já analisada anteriormente).")
                continue

            novas_vagas_processadas += 1
            print(f"\n🔍 Analisando nova vaga: '{vaga['titulo']}' - {vaga['empresa']}")

            # 4. Avalia a vaga com a IA (OpenAI gpt-4o-mini)
            resultado_ia = avaliar_vaga(
                titulo_vaga=vaga["titulo"],
                descricao_vaga=vaga["descricao"]
            )

            match = resultado_ia.get("match", False)
            score = resultado_ia.get("score", 0)
            resumo = resultado_ia.get("resumo", "Sem resumo informado.")
            pontos_fortes = resultado_ia.get("pontos_fortes", [])

            print(f"📊 Resultado IA -> Match: {match} | Score: {score}%")

            # 5. Se der Match e atingir a pontuação mínima, envia e-mail via iCloud
            if match and score >= 75:
                print(f"🎯 Vaga compatível encontrada! Disparando e-mail de notificação...")
                enviar_email_vaga(
                    titulo_vaga=vaga["titulo"],
                    empresa=vaga["empresa"],
                    url_vaga=vaga["url"],
                    resumo=resumo,
                    pontos_fortes=pontos_fortes
                )
            else:
                motivo = resultado_ia.get("motivo_rejeicao", "Critérios técnicos ou modelo não compatíveis.")
                print(f"🚫 Vaga descartada. Motivo: {motivo}")

            # 6. Registra no SQLite para não reprocessar no próximo ciclo
            db.salvar_vaga(
                vaga_id=vaga_id,
                titulo=vaga["titulo"],
                empresa=vaga["empresa"],
                url=vaga["url"],
                match=match,
                score=score
            )

        print(f"\n✅ Ciclo concluído. {novas_vagas_processadas} novas vagas foram processadas.")

    except Exception as e:
        print(f"❌ Ocorreu um erro durante o ciclo: {e}")

    finally:
        db.fechar()


def main():
    print("🚀 Agente de IA para Busca de Vagas Iniciado!")
    print(f"⏰ O agente executará verificações a cada {INTERVALO_HORAS} hora(s).\n")

    # Loop infinito para execução recorrente de hora em hora
    while True:
        executar_ciclo_agente()
        print(f"\n😴 Agente em repouso. Próxima checagem em {INTERVALO_HORAS} hora...")
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()