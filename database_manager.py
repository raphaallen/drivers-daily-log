import sqlite3
import os

# 1. Definir o caminho do banco de dados
DB_FILE = 'daily_log.db'

class DatabaseManager:
    """
    Gerencia a conexão e as operações de CRUD (Create, Read, Update, Delete)
    com o banco de dados SQLite.
    """

    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.conn = None
        self.cursor = None
        # Apenas inicializa, sem tentar se conectar aqui.

    def _connect(self):
        """Conecta-se ao banco de dados e garante que as tabelas existam."""
        try:
            # Garante que a conexão está fechada antes de abrir
            if self.conn:
                self.conn.close()
            
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            
            # CHAMA O SETUP AQUI: Garante que as tabelas são criadas
            self._setup_db() 
            
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")

    def _disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def _setup_db(self):
        """
        Cria as tabelas (Usuários e Log Diário) se elas não existirem.
        EXECUTA DIRETO, SEM CHAMAR _execute_query para evitar recursão.
        """
        
        # 1. Tabela de Usuários
        create_user_table = """
        CREATE TABLE IF NOT EXISTS Usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );
        """
        # 2. Tabela LogDiario (Com user_id e chave composta)
        create_log_table_query = """
        CREATE TABLE IF NOT EXISTS LogDiario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            data TEXT NOT NULL, 
            km_rodados REAL NOT NULL,
            faturamento_total REAL NOT NULL,
            horas_trabalhadas REAL NOT NULL,
            
            FOREIGN KEY (user_id) REFERENCES Usuarios(id),
            UNIQUE(user_id, data) 
        );
        """
        
        # Executa as queries diretamente na conexão ativa
        if self.cursor:
            self.cursor.execute(create_user_table)
            self.cursor.execute(create_log_table_query)
            self.conn.commit()


    def _execute_query(self, query, params=()):
        """
        Método auxiliar privado para executar uma query e tratar a conexão.
        Retorna o lastrowid (ID da linha inserida) ou True/False para outras operações.
        """
        self._connect()
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            
            # Se for uma inserção, retorna o ID da nova linha
            if query.strip().upper().startswith('INSERT'):
                return self.cursor.lastrowid
            
            return True # Retorna True para outras operações de sucesso
            
        except sqlite3.Error as e:
            # Não exibe a query, apenas a mensagem do erro para o usuário
            print(f"Erro na execução da query: {e}")
            return False 
        finally:
            self._disconnect()
            
            
    # --- MÉTODOS DE LOGIN/USUÁRIO ---
    
    def register_user(self, username, password):
        """Insere um novo usuário."""
        # NOTA DE SEGURANÇA: Em produção, o password NUNCA seria armazenado em texto puro. 
        # Deveríamos usar bcrypt/scrypt e armazenar um hash.
        query = "INSERT INTO Usuarios (username, password_hash) VALUES (?, ?)"
        # Retorna True se for inserido com sucesso, False se falhar (ex: usuário já existe)
        return self._execute_query(query, (username, password))

    def verify_login(self, username, password):
        """Verifica as credenciais e retorna o ID do usuário se for válido."""
        self._connect()
        try:
            self.cursor.execute("SELECT id, password_hash FROM Usuarios WHERE username = ?", (username,))
            result = self.cursor.fetchone()
            
            if result and result[1] == password:
                return result[0] # Retorna o user_id
            
            return None
        except sqlite3.Error as e:
            print(f"Erro ao verificar login: {e}")
            return None
        finally:
            self._disconnect()


    # --- MÉTODOS DE LOG DIÁRIO ---
    
    def upsert_daily_log(self, user_id, data, km_rodados, faturamento_total, horas_trabalhadas):
        """
        Atualiza ou insere um registro diário para o usuário e data específicos (UPSERT).
        """
        query = """
        INSERT OR REPLACE INTO LogDiario (user_id, data, km_rodados, faturamento_total, horas_trabalhadas)
        VALUES (?, ?, ?, ?, ?);
        """
        params = (user_id, data, km_rodados, faturamento_total, horas_trabalhadas) 
        
        print(f"\nTentando atualizar/inserir log para o Usuário {user_id}, Data: {data}")
        
        result = self._execute_query(query, params)
        
        if result:
            print("✅ Log diário atualizado/inserido com sucesso.")
            return True
        return False

    def get_daily_log(self, user_id, target_date):
        """Busca o log de um dia específico para o usuário."""
        self._connect()
        try:
            self.cursor.execute("SELECT km_rodados, faturamento_total, horas_trabalhadas FROM LogDiario WHERE user_id = ? AND data = ?", (user_id, target_date,))
            log = self.cursor.fetchone()
            return log # Retorna (km, faturamento, horas) ou None
        except sqlite3.Error as e:
            print(f"Erro ao buscar log: {e}")
            return None
        finally:
            self._disconnect()

    
    def get_all_logs_by_user(self, user_id):
        """Busca todos os logs de todos os dias para o usuário logado."""
        self._connect()
        try:
            query = "SELECT data, km_rodados, faturamento_total, horas_trabalhadas FROM LogDiario WHERE user_id = ? ORDER BY data DESC"
            self.cursor.execute(query, (user_id,))
            logs = self.cursor.fetchall()
            # logs será uma lista de tuplas: [('data', km, fat, hrs), ...]
            return logs
        except sqlite3.Error as e:
            print(f"Erro ao buscar todos os logs: {e}")
            return []
        finally:
            self._disconnect()