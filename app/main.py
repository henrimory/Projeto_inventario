"""
main.py - API principal do sistema
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid
import pytz
from datetime import datetime
from . import crud, schemas, logs, auth, middleware_auth
from .database import get_db, engine
from .models import Base
from pydantic import BaseModel

# =============================================
# CRIA AS TABELAS DO BANCO (executa uma vez)
# =============================================
Base.metadata.create_all(bind=engine)

# =============================================
# CRIA A APLICAÇÃO FASTAPI
# =============================================
app = FastAPI(
    title="Sistema de Gerenciamento de Parque de Computadores",
    description="CRUD completo com soft delete e logs de auditoria",
    version="1.0.0"
)

# =============================================
# CONFIGURAÇÃO DOS TEMPLATES (HTML)
# =============================================
templates = Jinja2Templates(directory="app/templates")

# =============================================
# MIDDLEWARE DE AUTENTICAÇÃO (protege as rotas)
# =============================================
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    response = middleware_auth.verificar_autenticacao(request)
    if response:
        return response
    return await call_next(request)

# =============================================
# INICIALIZAÇÃO (cria usuário admin)
# =============================================
@app.on_event("startup")
def startup():
    from .database import SessionLocal
    db = SessionLocal()
    auth.criar_usuario_admin(db)
    db.close()

# =============================================
# ROTAS DE AUTENTICAÇÃO (páginas e API)
# =============================================

@app.get("/login", response_class=HTMLResponse)
def pagina_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

class LoginSchema(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(login_data: LoginSchema, db: Session = Depends(get_db)):
    try:
        username = login_data.username
        password = login_data.password
        
        usuario = auth.autenticar_usuario(db, username, password)
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        token = str(uuid.uuid4())
        middleware_auth.salvar_sessao(token, username)
        
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_token", value=token, httponly=True)
        return response
    except Exception as e:
        print(f"Erro no login: {e}")
        raise HTTPException(status_code=401, detail="Erro ao fazer login")

@app.get("/logout")
def logout(response: Response):
    response.delete_cookie("session_token")
    return RedirectResponse(url="/login")

# =============================================
# ROTAS PARA INTERFACE WEB (HTML)
# =============================================

@app.get("/", response_class=HTMLResponse)
def pagina_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/computadores", response_class=HTMLResponse)
def pagina_computadores(request: Request):
    return templates.TemplateResponse("computadores.html", {"request": request})

@app.get("/computadores/novo", response_class=HTMLResponse)
def pagina_novo_computador(request: Request):
    return templates.TemplateResponse("form_computador.html", {"request": request, "computador": None})

@app.get("/computadores/{computador_id}/editar", response_class=HTMLResponse)
def pagina_editar_computador(request: Request, computador_id: int, db: Session = Depends(get_db)):
    computador = crud.buscar_computador_por_id(db, computador_id)
    return templates.TemplateResponse("form_computador.html", {"request": request, "computador": computador})

@app.get("/logs", response_class=HTMLResponse)
def pagina_logs(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/relatorios", response_class=HTMLResponse)
def pagina_relatorios(request: Request):
    return templates.TemplateResponse("relatorios.html", {"request": request})

# =============================================
# ROTAS DA API (seus endpoints originais)
# =============================================

@app.post("/computadores/", response_model=schemas.ComputadorResponse, status_code=status.HTTP_201_CREATED)
def criar_computador(computador: schemas.ComputadorCreate, db: Session = Depends(get_db)):
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
    return crud.listar_computadores(db, ativo=ativo, skip=skip, limit=limit)

@app.get("/computadores/{computador_id}", response_model=schemas.ComputadorResponse)
def buscar_computador(computador_id: int, db: Session = Depends(get_db)):
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
    computador_antigo = crud.buscar_computador_por_id(db, computador_id)
    if not computador_antigo:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    valores_antigos = {c.name: getattr(computador_antigo, c.name) for c in computador_antigo.__table__.columns}
    
    computador_novo = crud.atualizar_computador(db, computador_id, computador_update)
    
    valores_novos = {c.name: getattr(computador_novo, c.name) for c in computador_novo.__table__.columns}
    
    logs.registrar_log_comparativo(
        db=db, tabela="computadores", registro_id=computador_id,
        dados_antigos=valores_antigos, dados_novos=valores_novos, usuario="sistema"
    )
    
    db.commit()
    return computador_novo

@app.delete("/computadores/{computador_id}")
def desativar_computador(computador_id: int, db: Session = Depends(get_db)):
    computador = crud.desativar_computador(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    logs.registrar_log(db, "computadores", computador_id, "ativo", True, False, "sistema")
    db.commit()
    return {"message": "Computador desativado com sucesso"}

@app.patch("/computadores/{computador_id}/reativar")
def reativar_computador(computador_id: int, db: Session = Depends(get_db)):
    computador = crud.ativar_computador(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    logs.registrar_log(db, "computadores", computador_id, "ativo", False, True, "sistema")
    db.commit()
    return {"message": "Computador reativado com sucesso"}

@app.get("/logs/")
def listar_logs(limite: int = 50, db: Session = Depends(get_db)):
    return logs.buscar_logs_recentes(db, limite)

@app.get("/computadores/{computador_id}/logs/")
def buscar_logs_do_computador(computador_id: int, db: Session = Depends(get_db)):
    computador = crud.buscar_computador_por_id(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    return logs.buscar_logs_por_registro(db, "computadores", computador_id)

# =============================================
# ROTAS DA API
# =============================================

@app.get("/api/computadores/", response_model=List[schemas.ComputadorResponse])
def api_listar_computadores(
    ativo: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud.listar_computadores(db, ativo=ativo, skip=skip, limit=limit)


@app.post("/api/computadores/", response_model=schemas.ComputadorResponse, status_code=status.HTTP_201_CREATED)
def api_criar_computador(computador: schemas.ComputadorCreate, db: Session = Depends(get_db)):
    # Verifica se patrimônio já existe
    existente = crud.buscar_computador_por_patrimonio(db, computador.patrimonio)
    if existente:
        raise HTTPException(status_code=400, detail="Patrimônio já cadastrado")
    return crud.criar_computador(db, computador)


@app.get("/api/computadores/{computador_id}", response_model=schemas.ComputadorResponse)
def api_buscar_computador(computador_id: int, db: Session = Depends(get_db)):
    computador = crud.buscar_computador_por_id(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    return computador


@app.put("/api/computadores/{computador_id}", response_model=schemas.ComputadorResponse)
def api_atualizar_computador(
    computador_id: int,
    computador_update: schemas.ComputadorUpdate,
    db: Session = Depends(get_db)
):
    computador_antigo = crud.buscar_computador_por_id(db, computador_id)
    if not computador_antigo:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    # Guarda valores antigos para log
    valores_antigos = {c.name: getattr(computador_antigo, c.name) for c in computador_antigo.__table__.columns}
    
    computador_novo = crud.atualizar_computador(db, computador_id, computador_update)
    if not computador_novo:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    # Guarda valores novos para log
    valores_novos = {c.name: getattr(computador_novo, c.name) for c in computador_novo.__table__.columns}
    
    # Registra logs
    logs.registrar_log_comparativo(
        db=db, tabela="computadores", registro_id=computador_id,
        dados_antigos=valores_antigos, dados_novos=valores_novos, usuario="sistema"
    )
    
    db.commit()
    return computador_novo


@app.delete("/api/computadores/{computador_id}")
def api_desativar_computador(computador_id: int, db: Session = Depends(get_db)):
    computador = crud.desativar_computador(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    logs.registrar_log(db, "computadores", computador_id, "ativo", True, False, "sistema")
    db.commit()
    return {"message": "Computador desativado com sucesso"}


@app.patch("/api/computadores/{computador_id}/reativar")
def api_reativar_computador(computador_id: int, db: Session = Depends(get_db)):
    computador = crud.ativar_computador(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    
    logs.registrar_log(db, "computadores", computador_id, "ativo", False, True, "sistema")
    db.commit()
    return {"message": "Computador reativado com sucesso"}


@app.get("/api/logs/")
def api_listar_logs(limite: int = 1000, db: Session = Depends(get_db)):
    logs_lista = logs.buscar_logs_recentes(db, limite)
    
    # Converte para dicionário com data formatada
    resultado = []
    for log in logs_lista:
        resultado.append({
            "id": log.id,
            "tabela": log.tabela,
            "registro_id": log.registro_id,
            "campo": log.campo,
            "valor_antigo": log.valor_antigo,
            "valor_novo": log.valor_novo,
            "usuario": log.usuario,
            "data_hora": formatar_data_br(log.data_hora)  # Data já formatada
        })
    
    return resultado


@app.get("/api/computadores/{computador_id}/logs/")
def api_buscar_logs_do_computador(computador_id: int, db: Session = Depends(get_db)):
    computador = crud.buscar_computador_por_id(db, computador_id)
    if not computador:
        raise HTTPException(status_code=404, detail="Computador não encontrado")
    return logs.buscar_logs_por_registro(db, "computadores", computador_id)


def formatar_data_br(data):
    """Converte datetime para string no formato brasileiro (horário de SP)"""
    if data:
        # Se a data não tem timezone, adiciona o timezone de SP
        if data.tzinfo is None:
            sp_tz = pytz.timezone('America/Sao_Paulo')
            data = sp_tz.localize(data)
        
        # Converte para o horário de SP e formata
        sp_tz = pytz.timezone('America/Sao_Paulo')
        data_sp = data.astimezone(sp_tz)
        return data_sp.strftime("%d/%m/%Y %H:%M:%S")
    return ""