import sqlite3


class Database:
    def __init__(self, db_path="vagas.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.criar_tabela()

    def criar_tabela(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vagas_processadas (
                id TEXT PRIMARY KEY,
                titulo TEXT,
                empresa TEXT,
                url TEXT,
                match BOOLEAN,
                score INTEGER,
                data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def vaga_ja_processada(self, vaga_id: str, url: str = None) -> bool:
        """
        Verifica se a vaga já foi analisada pelo ID ou pela URL exata.
        """
        cursor = self.conn.cursor()
        
        # 1. Checa por ID
        cursor.execute("SELECT 1 FROM vagas_processadas WHERE id = ?", (vaga_id,))
        if cursor.fetchone():
            return True

        # 2. Checa por URL (se informada) para evitar duplicatas com IDs diferentes
        if url:
            cursor.execute("SELECT 1 FROM vagas_processadas WHERE url = ?", (url,))
            if cursor.fetchone():
                return True

        return False

    def salvar_vaga(self, vaga_id: str, titulo: str, empresa: str, url: str, match: bool, score: int):
        """
        Registra a vaga como processada no banco local.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO vagas_processadas (id, titulo, empresa, url, match, score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vaga_id, titulo, empresa, url, match, score))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # Vaga já existia no banco

    def fechar(self):
        self.conn.close()