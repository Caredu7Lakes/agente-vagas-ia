import requests

from src.config import settings

BASE_URL = "https://ntfy.sh"


class NotifyService:
    def __init__(self):
        self.topic = settings.NTFY_TOPIC

    @property
    def habilitado(self) -> bool:
        return bool(self.topic)

    def send_notification(self, title: str, message: str) -> bool:
        """Envia push via ntfy.sh. Nunca levanta exceção."""
        if not self.habilitado:
            print("⚠️ Notificação desabilitada: NTFY_TOPIC ausente.")
            return False

        try:
            response = requests.post(
                f"{BASE_URL}/{self.topic}",
                data=message.encode("utf-8"),
                headers={
                    "Title": title.encode("utf-8"),
                    "Tags": "briefcase",
                    "Priority": "default",
                },
                timeout=15,
            )
            response.raise_for_status()
            print("📲 Notificação enviada.")
            return True
        except requests.RequestException as e:
            print(f"❌ Falha ao notificar: {type(e).__name__}")
            return False