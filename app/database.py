"""
database.py - Conexão com o banco de dados
============================================
Este arquivo configura a ponte entre o Python e o banco SQLite.
Toda comunicação com o banco passa por aqui.

Autor: Henrique Oliveira
Data: 06/2026
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carrega configurações do arquivo .env (segurança)
load_dotenv()

# URL do banco de dados (SQLite = arquivo local)
# O banco será salvo como "inventario.db" na pasta raiz
DATABASE_URL = "sqlite:///./inventario.db"

# Cria o motor de conexão (o "motor" que conversa com o banco)
engine = create_engine(
    DATABASE_URL,
    # SQLite precisa disso para funcionar com múltiplas requisições
    connect_args={"check_same_thread": False}
)

# Cria a fábrica de sessões (cria conexões sob demanda)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base para criação das tabelas (todas herdarão dela)
Base = declarative_base()

# Função que fornece uma sessão do banco para cada requisição
def get_db():
    """Cria e gerencia uma conexão com o banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()