"""
logs.py - Sistema de auditoria
================================
Registra automaticamente todas as alterações feitas nos registros.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from . import models


def registrar_log(
    db: Session,
    tabela: str,
    registro_id: int,
    campo: str,
    valor_antigo: Optional[Any],
    valor_novo: Optional[Any],
    usuario: str = "sistema"
):
    """Registra uma alteração na tabela de logs."""
    
    valor_antigo_str = str(valor_antigo) if valor_antigo is not None else ""
    valor_novo_str = str(valor_novo) if valor_novo is not None else ""
    
    if valor_antigo_str == valor_novo_str:
        return
    
    log = models.LogEdicao(
        tabela=tabela,
        registro_id=registro_id,
        campo=campo,
        valor_antigo=valor_antigo_str,
        valor_novo=valor_novo_str,
        usuario=usuario
    )
    
    db.add(log)


def registrar_log_comparativo(
    db: Session,
    tabela: str,
    registro_id: int,
    dados_antigos: Dict[str, Any],
    dados_novos: Dict[str, Any],
    usuario: str = "sistema"
):
    """Compara dois dicionários e registra TODAS as diferenças."""
    
    for campo in dados_novos.keys():
        if campo in ['id', 'created_at', 'updated_at']:
            continue
        
        valor_antigo = dados_antigos.get(campo)
        valor_novo = dados_novos.get(campo)
        
        registrar_log(
            db=db,
            tabela=tabela,
            registro_id=registro_id,
            campo=campo,
            valor_antigo=valor_antigo,
            valor_novo=valor_novo,
            usuario=usuario
        )


def buscar_logs_por_registro(db: Session, tabela: str, registro_id: int):
    """Retorna todos os logs de um registro específico."""
    return db.query(models.LogEdicao).filter(
        models.LogEdicao.tabela == tabela,
        models.LogEdicao.registro_id == registro_id
    ).order_by(models.LogEdicao.data_hora.desc()).all()


def buscar_logs_recentes(db: Session, limite: int = 50):
    """Retorna os logs mais recentes."""
    return db.query(models.LogEdicao).order_by(
        models.LogEdicao.data_hora.desc()
    ).limit(limite).all()
