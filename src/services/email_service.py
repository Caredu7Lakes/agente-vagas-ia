import socket
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

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
        """Busca e-mails não lidos contendo a palavra-chave especificada."""
        mail = self.connect_imap()
        if not mail:
            return []

        vagas = []
        try:
            mail.select("INBOX")
            # Busca e-mails não lidos
            status, messages = mail.search(None, f'(UNSEEN BODY "{search_keyword}")')

            if status != "OK" or not messages or not messages[0]:
                print(f"ℹ️ Nenhum e-mail não lido encontrado para o termo '{search_keyword}'.")
                mail.logout()
                return []

            email_ids = messages[0].split()
            print(f"📧 {len(email_ids)} e-mail(s) não lido(s) encontrado(s). Processando...")

            for e_id in email_ids:
                status, msg_data = mail.fetch(e_id, "(RFC822)")
                if status != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = msg.get("Subject", "")
                        sender = msg.get("From", "")
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                        vagas.append({
                            "id": e_id.decode(),
                            "subject": subject,
                            "sender": sender,
                            "body": body
                        })

            mail.logout()
        except Exception as e:
            print(f"❌ Erro ao buscar e-mails: {e}")

        return vagas

    def send_application_email(self, to_email, subject, body_text, attachment_path=None):
        """Envia o e-mail de candidatura via SMTP com anexo opcional."""
        if not self.email_user or not self.email_pass:
            print("❌ Erro: EMAIL_USER ou EMAIL_PASS não configurados!")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body_text, "plain"))

            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=filename)
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.sendmail(self.email_user, to_email, msg.as_string())
            server.quit()

            print(f"✅ E-mail enviado com sucesso para {to_email}")
            return True
        except Exception as e:
            print(f"❌ Erro ao enviar e-mail via SMTP: {e}")
            return False