from supabase import create_client, Client
import os
import logging

# Configuração básica do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupabaseClient")

url = os.getenv("SUPABASE_DB_URL")
key = os.getenv("SUPABASE_DB_PASS")

class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)
        logger.info("SupabaseClient inicializado.")

    def insert(self, table: str, data: dict):
        logger.info(f"Inserindo dados na tabela '{table}': {data}")
        response = self.supabase.table(table).insert(data).execute()
        logger.info(f"Resposta do insert: {response.data}")
        return response.data

    def select(self, table: str, filters: dict = None):
        logger.info(f"Consultando tabela '{table}' com filtros: {filters}")
        query = self.supabase.table(table).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        logger.info(f"Resposta do select: {response.data}")
        return response.data

    def update(self, table: str, filters: dict, data: dict):
        logger.info(f"Atualizando tabela '{table}' com filtros: {filters} e dados: {data}")
        query = self.supabase.table(table)
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.update(data).execute()
        logger.info(f"Resposta do update: {response.data}")
        return response.data

    def delete(self, table: str, filters: dict):
        logger.info(f"Deletando da tabela '{table}' com filtros: {filters}")
        query = self.supabase.table(table)
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.delete().execute()
        logger.info(f"Resposta do delete: {response.data}")
        return response.data