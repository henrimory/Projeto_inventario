"""
main.py - API principal do sistema
====================================
Define todas as rotas (endpoints) que o sistema vai responder.
Cada rota executa uma função do crud.py e retorna o resultado.

Autor: Seu Nome
Data: 2026
"""

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from . import crud, schemas, logs
from .database import get_db, engine
from .models import Base

# Cria as tabelas se não existirem (executa uma vez)
Base.metadata.create_all(bind=engine)

# Cria a aplicação FastAPI
app = FastAPI(
    title="Sistema de Gerenciamento de Parque de Computadores",
    description="CRUD completo com soft delete e logs de auditoria",
    version="1.0.0"
)


# =============================================
# ROTAS PARA COMPUTADORES
# =============================================

@app.post("/computadores/", response_model=schemas.ComputadorResponse, status_code=status.HTTP_201_CREATED)
def criar_computador(computador: schemas.ComputadorCreate, db: Session = Depends(get_db)):
    """
    Cria um novo computador.
    
    - **patrimonio**: Número único do patrimônio (obrigatório)
    - **nome**: Nome do computador (obrigatório)
    - **status**: Disponível, Em uso ou Manutenção (padrão: Disponível)
    """
    # Verifica se patrimônio já existe
    existente = crud.buscar_computador_por_patrimonio(db, computador.patrimonio)
    if existente:
        raise HTTPException(status_code=400, detail="Patrimônio já cadastrado")
    
    return crud.criar_computador(db, computador)


@app.get("/computadores/", response_model=List[schemas.ComputadorResponse])
def listar_computadores(
    ativo: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Lista todos os computadores.
    
    - **ativo**: True (apenas ativos), False (apenas inativos), None (todos)
    - **skip**: Quantos pular (paginação)
    - **limit**: Máximo de resultados
    """
    return crud.listar_computadores(db, ativo=ativo, skip=skip, limit=limit)


@app.get("/computadores/{computador_id}", response_model=schemas.ComputadorResponse)
def buscar_computador(computador_id: int, db: Session = Depends(get_db)):
    """
    Busca um computador pelo ID.
    """
    computador = crud.buscar_computador_por_id(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    return computador


@app.put("/computadores/{computador_id}", response_model=schemas.ComputadorResponse)
def atualizar_computador(
    computador_id: int,
    computador_update: schemas.ComputadorUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza um computador existente.
    
    - Envie apenas os campos que deseja alterar
    - Registra automaticamente TODAS as alterações nos logs
    """
    # Busca o computador original (para comparar depois)
    computador_antigo = crud.buscar_computador_por_id(db, computador_id)
    if not computador_antigo:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    # Guarda os valores antigos como dicionário
    valores_antigos = {
        "patrimonio": computador_antigo.patrimonio,
        "nome": computador_antigo.nome,
        "marca": computador_antigo.marca,
        "modelo": computador_antigo.modelo,
        "processador": computador_antigo.processador,
        "memoria_ram": computador_antigo.memoria_ram,
        "armazenamento": computador_antigo.armazenamento,
        "status": computador_antigo.status,
        "localizacao": computador_antigo.localizacao,
        "usuario_responsavel": computador_antigo.usuario_responsavel,
        "ativo": computador_antigo.ativo
    }
    
    # Atualiza o computador
    computador_novo = crud.atualizar_computador(db, computador_id, computador_update)
    
    # Guarda os valores novos
    valores_novos = {
        "patrimonio": computador_novo.patrimonio,
        "nome": computador_novo.nome,
        "marca": computador_novo.marca,
        "modelo": computador_novo.modelo,
        "processador": computador_novo.processador,
        "memoria_ram": computador_novo.memoria_ram,
        "armazenamento": computador_novo.armazenamento,
        "status": computador_novo.status,
        "localizacao": computador_novo.localizacao,
        "usuario_responsavel": computador_novo.usuario_responsavel,
        "ativo": computador_novo.ativo
    }
    
    # Registra as alterações nos logs
    logs.registrar_log_comparativo(
        db=db,
        tabela="computadores",
        registro_id=computador_id,
        dados_antigos=valores_antigos,
        dados_novos=valores_novos,
        usuario="sistema"  # TODO: implementar autenticação
    )
    
    db.commit()
    return computador_novo


@app.delete("/computadores/{computador_id}")
def desativar_computador(computador_id: int, db: Session = Depends(get_db)):
    """
    Desativa um computador (soft delete).
    
    O computador não é excluído, apenas marcado como inativo.
    Para reativar, use o endpoint PATCH /computadores/{id}/ativar
    """
    computador = crud.desativar_computador(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    # Registra o log da desativação
    logs.registrar_log(
        db=db,
        tabela="computadores",
        registro_id=computador_id,
        campo="ativo",
        valor_antigo=True,
        valor_novo=False,
        usuario="sistema"
    )
    
    db.commit()
    return {"message": "Computador desativado com sucesso"}


@app.patch("/computadores/{computador_id}/ativar")
def reativar_computador(computador_id: int, db: Session = Depends(get_db)):
    """
    Reativa um computador que estava desativado.
    """
    computador = crud.ativar_computador(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    logs.registrar_log(
        db=db,
        tabela="computadores",
        registro_id=computador_id,
        campo="ativo",
        valor_antigo=False,
        valor_novo=True,
        usuario="sistema"
    )
    
    db.commit()
    return {"message": "Computador reativado com sucesso"}


# =============================================
# ROTAS PARA LOGS
# =============================================

@app.get("/logs/")
def listar_logs(limite: int = 50, db: Session = Depends(get_db)):
    """
    Lista os logs mais recentes do sistema.
    """
    return logs.buscar_logs_recentes(db, limite)


@app.get("/computadores/{computador_id}/logs/")
def buscar_logs_do_computador(computador_id: int, db: Session = Depends(get_db)):
    """
    Retorna o histórico completo de edições de um computador específico.
    """
    # Verifica se o computador existe
    computador = crud.buscar_computador_por_id(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    return logs.buscar_logs_por_registro(db, "computadores", computador_id)


# =============================================
# ROTA RAIZ (apenas para teste)
# =============================================

@app.get("/")
def raiz():
    """
    Rota inicial para verificar se a API está funcionando.
    """
    return {
        "mensagem": "Sistema de Gerenciamento de Parque de Computadores",
        "versao": "1.0.0",
        "endpoints": {
            "computadores": "/computadores/",
            "logs": "/logs/"
        }
    }