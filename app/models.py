"""
models.py - Estrutura das tabelas do banco de dados
=====================================================
Define como os dados serão organizados no banco.
Cada classe = uma tabela. Cada atributo = uma coluna.

Autor: Henrique Oliveira
Data: 06/2026
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
import pytz
from .database import Base
from datetime import datetime


class Usuario(Base):
    """
    Tabela de usuários do sistema
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)  # Hash da senha (nunca armazenar senha pura)
    nome_completo = Column(String, nullable=False)
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Computador(Base):
    """
    Tabela de computadores (soft delete = não exclui, apenas desativa)
    """
    __tablename__ = "computadores"

    # Identificador único (automático)
    id = Column(Integer, primary_key=True, index=True)

    # Dados principais
    patrimonio = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, nullable=False)
    marca = Column(String, nullable=True)
    modelo = Column(String, nullable=True)
    processador = Column(String, nullable=True)
    memoria_ram = Column(String, nullable=True)  # Ex: "8GB", "16GB"
    armazenamento = Column(String, nullable=True)  # Ex: "512GB SSD"

    # Status e localização
    status = Column(String, default="Disponível")  # Disponível, Em uso, Manutenção
    localizacao = Column(String, nullable=True)  # Sala, setor
    usuario_responsavel = Column(String, nullable=True)

    # Soft delete (False = desativado, não excluído)
    ativo = Column(Boolean, default=True)

    # Controle de datas
    data_aquisicao = Column(DateTime, default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Função para pegar horário de São Paulo
def get_sp_time():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

class LogEdicao(Base):
    __tablename__ = "logs_edicoes"

    id = Column(Integer, primary_key=True, index=True)
    tabela = Column(String)
    registro_id = Column(Integer)
    campo = Column(String)
    valor_antigo = Column(Text, nullable=True)
    valor_novo = Column(Text, nullable=True)
    usuario = Column(String, default="sistema")
    data_hora = Column(DateTime(timezone=True), default=get_sp_time)  # ← Alterado