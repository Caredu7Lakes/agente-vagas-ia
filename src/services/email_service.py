import email
import imaplib
import os
import re
import smtplib
import socket
from email.header import decode_header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import settings


class EmailReaderService:
    def __init__(self):
        self.email_user = settings.EMAIL_USER
        self.email_pass = settings.EMAIL_PASS
        self.imap_server = settings.IMAP_SERVER
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT

    def connect_imap(self):
        """Conecta ao servidor IMAP com SSL para leitura de e-mails."""
        host = self.imap_server.strip()
        print(f"🔌 Conectando IMAP em {host!r} como {self.email_user!r}")

        try:
            mail = imaplib.IMAP4_SSL(host, 993, timeout=30)
            mail.login(self.email_user, self.email_pass)
            return mail
        except socket.gaierror as e:
            raise RuntimeError(f"Host IMAP não resolve: {host!r}") from e
        except imaplib.IMAP4.error as e:
            raise RuntimeError("Login IMAP recusado — senha de app do iCloud?") from e
    def fetch_unread_job_emails(self, search_keyword="vaga"):
        """Busca e-mails não lidos e filtra por palavra-chave localmente.

        O filtro é feito em Python porque o iCloud aceita critérios IMAP como
        SUBJECT/BODY/FROM mas retorna resultado vazio sem sinalizar erro.
        """
        mail = self.connect_imap()
        if not mail:
            return []

        vagas = []
        termo = search_keyword.lower()

        try:
            mail.select("INBOX")
            status, messages = mail.search(None, "UNSEEN")

            if status != "OK" or not messages or not messages[0]:
                print("ℹ️ Nenhum e-mail não lido na caixa de entrada.")
                mail.logout()
                return []

            ids = messages[0].split()
            print(f"📧 {len(ids)} e-mail(s) não lido(s). Filtrando por '{search_keyword}'...")

            for e_id in ids:
                status, msg_data = mail.fetch(e_id, "(BODY.PEEK[])")
                if status != "OK":
                    continue

                for response_part in msg_data:
                    if not isinstance(response_part, tuple):
                        continue

                    msg = email.message_from_bytes(response_part[1])

                    subject = self._decodificar_cabecalho(msg.get("Subject", ""))
                    sender = self._decodificar_cabecalho(msg.get("From", ""))

                    body = ""
                    body_html = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_maintype() == "multipart":
                                continue
                            if part.get("Content-Disposition", "").startswith("attachment"):
                                continue

                            payload = part.get_payload(decode=True)
                            if not payload:
                                continue
                            texto = payload.decode("utf-8", errors="ignore")

                            if part.get_content_type() == "text/plain" and not body:
                                body = texto
                            elif part.get_content_type() == "text/html" and not body_html:
                                body_html = texto
                    else:
                        payload = msg.get_payload(decode=True)
                        body = payload.decode("utf-8", errors="ignore") if payload else ""

                    if not body:
                        body = re.sub(r"<[^>]+>", " ", body_html)

                    if termo not in f"{subject} {body}".lower():
                        continue

                    vagas.append({
                        "id": e_id.decode(),
                        "subject": subject,
                        "sender": sender,
                        "body": body,
                    })

            print(f"🎯 {len(vagas)} e-mail(s) de vaga identificado(s).")
            mail.logout()
        except Exception as e:
            print(f"❌ Erro ao buscar e-mails: {type(e).__name__}: {e}")

        return vagas

    @staticmethod
    def _decodificar_cabecalho(valor: str) -> str:
        """Decodifica cabeçalhos MIME (=?UTF-8?B?...?=) para texto legível."""
        partes = []
        for texto, charset in decode_header(valor):
            if isinstance(texto, bytes):
                partes.append(texto.decode(charset or "utf-8", errors="ignore"))
            else:
                partes.append(texto)
        return "".join(partes)
      
    def send_application_email(self, to_email, subject, cover_letter, cv_path=None):
        """Envia o e-mail de candidatura via SMTP com anexo opcional."""
        if not self.email_user or not self.email_pass:
            print("❌ Erro: EMAIL_USER ou EMAIL_PASS não configurados!")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(cover_letter, "plain"))

            if cv_path and os.path.exists(cv_path):
                filename = os.path.basename(cv_path)
                with open(cv_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=filename)
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)
            elif cv_path:
                print(f"⚠️ Anexo não encontrado: {cv_path} — envio abortado.")
                return False

            destinatarios = [to_email]
            if settings.EMAIL_BCC:
                destinatarios.append(settings.EMAIL_BCC)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.sendmail(self.email_user, destinatarios, msg.as_string())
            server.quit()

            print(f"✅ Candidatura enviada para {to_email}" + (" (BCC ativo)" if settings.EMAIL_BCC else ""))
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar e-mail via SMTP: {type(e).__name__}: {e}")
            return False