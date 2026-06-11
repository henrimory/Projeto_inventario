"""
models.py - Estrutura das tabelas do banco de dados
=====================================================
Define como os dados serão organizados no banco.
Cada classe = uma tabela. Cada atributo = uma coluna.

Autor: Henrique Oliveira
Data: 06/2026
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .database import Base


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


class LogEdicao(Base):
    """
    Tabela de auditoria - guarda histórico de todas as alterações
    """
    __tablename__ = "logs_edicoes"

    id = Column(Integer, primary_key=True, index=True)
    tabela = Column(String)  # Nome da tabela alterada (ex: "computadores")
    registro_id = Column(Integer)  # ID do registro alterado
    campo = Column(String)  # Nome do campo modificado
    valor_antigo = Column(Text, nullable=True)  # Valor antes da alteração
    valor_novo = Column(Text, nullable=True)  # Valor depois da alteração
    usuario = Column(String, default="sistema")  # Quem fez a alteração
    data_hora = Column(DateTime(timezone=True), server_default=func.now())