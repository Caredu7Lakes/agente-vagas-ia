import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import settings


def enviar_email_vaga(titulo_vaga: str, empresa: str, url_vaga: str, resumo: str, pontos_fortes: list):
    sender = settings.EMAIL_USER
    password = settings.EMAIL_PASS
    receiver = settings.EMAIL_RECEIVER

 # Configurações do servidor SMTP do iCloud
    smtp_host = settings.SMTP_SERVER
    smtp_port = settings.SMTP_PORT

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"🚀 [VAGA ENCONTRADA] {titulo_vaga} - {empresa}"

    pontos_html = "".join([f"<li>{p}</li>" for p in pontos_fortes])

    corpo_html = f"""
    <h2>🎯 Nova Vaga Compatível Encontrada!</h2>
    <p><strong>Vaga:</strong> {titulo_vaga}</p>
    <p><strong>Empresa:</strong> {empresa}</p>
    <p><strong>Resumo IA:</strong> {resumo}</p>
    
    <h3>Pontos Fortes do seu Perfil:</h3>
    <ul>{pontos_html}</ul>
    
    <p><a href="{url_vaga}" style="background-color: #007aff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Ver Vaga / Clicar para Aplicar</a></p>
    <p><strong>Link:</strong> {url_vaga}</p>
    """

    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Requerido pelo iCloud
            server.login(sender, password)
            server.send_message(msg)
            print("✅ E-mail enviado com sucesso via iCloud!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
