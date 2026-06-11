"""
crud.py - Operações de banco (CRUD)
=====================================
Contém todas as funções que interagem com o banco de dados.
Cada função é uma operação específica.

Autor: Seu Nome
Data: 2026
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas


# =============================================
# OPERAÇÕES DE CREATE (Criar)
# =============================================

def criar_computador(db: Session, computador: schemas.ComputadorCreate):
    """
    Cria um novo computador no banco
    """
    # Converte o schema recebido em um modelo do banco
    db_computador = models.Computador(**computador.model_dump())
    db.add(db_computador)  # Adiciona na sessão
    db.commit()           # Salva no banco
    db.refresh(db_computador)  # Atualiza com dados do banco (ex: ID)
    return db_computador


# =============================================
# OPERAÇÕES DE READ (Ler)
# =============================================

def listar_computadores(db: Session, ativo: Optional[bool] = None, skip: int = 0, limit: int = 100):
    """
    Lista computadores com filtros opcionais
    - ativo: se True, só ativos. Se False, só inativos. Se None, todos.
    - skip: quantos pular (para paginação)
    - limit: máximo de resultados
    """
    query = db.query(models.Computador)
    
    if ativo is not None:
        query = query.filter(models.Computador.ativo == ativo)
    
    return query.offset(skip).limit(limit).all()


def buscar_computador_por_id(db: Session, computador_id: int):
    """
    Busca um computador específico pelo ID
    Retorna None se não existir
    """
    return db.query(models.Computador).filter(models.Computador.id == computador_id).first()


def buscar_computador_por_patrimonio(db: Session, patrimonio: str):
    """
    Busca um computador pelo número de patrimônio
    Retorna None se não existir
    """
    return db.query(models.Computador).filter(models.Computador.patrimonio == patrimonio).first()


# =============================================
# OPERAÇÕES DE UPDATE (Atualizar)
# =============================================

def atualizar_computador(db: Session, computador_id: int, computador_update: schemas.ComputadorUpdate):
    """
    Atualiza um computador existente
    Retorna None se computador não existir
    """
    # Busca o computador
    db_computador = buscar_computador_por_id(db, computador_id)
    if not db_computador:
        return None
    
    # Pega apenas os campos que foram enviados (não nulos)
    update_data = computador_update.model_dump(exclude_unset=True)
    
    # Atualiza cada campo
    for field, value in update_data.items():
        setattr(db_computador, field, value)
    
    db.commit()
    db.refresh(db_computador)
    return db_computador


def desativar_computador(db: Session, computador_id: int):
    """
    Soft delete - desativa o computador em vez de excluir
    """
    db_computador = buscar_computador_por_id(db, computador_id)
    if not db_computador:
        return None
    
    db_computador.ativo = False
    db.commit()
    db.refresh(db_computador)
    return db_computador


def ativar_computador(db: Session, computador_id: int):
    """
    Reativa um computador desativado
    """
    db_computador = buscar_computador_por_id(db, computador_id)
    if not db_computador:
        return None
    
    db_computador.ativo = True
    db.commit()
    db.refresh(db_computador)
    return db_computador


# =============================================
# OPERAÇÕES DE DELETE (Excluir - REAL)
# =============================================

def excluir_computador_permanente(db: Session, computador_id: int):
    """
    Exclusão REAL (permanente). Use com cuidado!
    Retorna True se excluiu, False se não existia
    """
    db_computador = buscar_computador_por_id(db, computador_id)
    if not db_computador:
        return False
    
    db.delete(db_computador)
    db.commit()
    return True