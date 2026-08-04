import os

from dotenv import load_dotenv

load_dotenv()  # no-op no CI, onde as vars vêm do env do runner


class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
    EMAIL_BCC = os.getenv("EMAIL_BCC")
    IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.mail.me.com")
    SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.mail.me.com")
    SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

    ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
    ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

    NTFY_TOPIC = os.getenv("NTFY_TOPIC")

    OBRIGATORIAS = ("OPENAI_API_KEY", "EMAIL_USER", "EMAIL_PASS")

    @classmethod
    def validar(cls) -> None:
        faltando = [k for k in cls.OBRIGATORIAS if not getattr(cls, k)]
        if faltando:
            raise RuntimeError(f"Variáveis de ambiente ausentes: {faltando}")


settings = Settings()