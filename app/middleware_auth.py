"""
middleware_auth.py - Controle de sessão e proteção de rotas
"""
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import json
import os

# Arquivo para simular sessão (em produção, usar Redis ou banco)
SESSION_FILE = "sessoes.json"

def salvar_sessao(token: str, username: str):
    """Salva uma sessão ativa"""
    sessoes = {}
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            sessoes = json.load(f)
    
    sessoes[token] = username
    with open(SESSION_FILE, 'w') as f:
        json.dump(sessoes, f)

def validar_sessao(token: str) -> bool:
    """Verifica se a sessão é válida"""
    if not token:
        return False
    
    if not os.path.exists(SESSION_FILE):
        return False
    
    with open(SESSION_FILE, 'r') as f:
        sessoes = json.load(f)
    
    return token in sessoes

def remover_sessao(token: str):
    """Remove uma sessão (logout)"""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            sessoes = json.load(f)
        
        if token in sessoes:
            del sessoes[token]
            with open(SESSION_FILE, 'w') as f:
                json.dump(sessoes, f)

def verificar_autenticacao(request: Request):
    """Middleware para proteger rotas"""
    token = request.cookies.get("session_token")
    
    # Rotas públicas (não exigem login)
    rotas_publicas = ["/login", "/static", "/api/login", "/docs", "/openapi.json", "/redoc"]
    
    if request.url.path in rotas_publicas or request.url.path.startswith("/static"):
        return None
    
    if not validar_sessao(token):
        return RedirectResponse(url="/login", status_code=302)
    
    return None