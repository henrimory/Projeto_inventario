"""
auth.py - Autenticação e gerenciamento de usuários
"""
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models

# Configuração de hash de senha (bcrypt é seguro)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str) -> str:
    """Gera hash da senha"""
    return pwd_context.hash(senha)

def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return pwd_context.verify(senha, senha_hash)

def autenticar_usuario(db: Session, username: str, senha: str):
    """Autentica um usuário"""
    usuario = db.query(models.Usuario).filter(
        models.Usuario.username == username,
        models.Usuario.ativo == True
    ).first()
    
    if not usuario:
        return None
    
    if not verificar_senha(senha, usuario.senha_hash):
        return None
    
    return usuario

def criar_usuario_admin(db: Session):
    """Cria usuário admin padrão se não existir"""
    usuario = db.query(models.Usuario).filter(models.Usuario.username == "admin").first()
    if not usuario:
        admin = models.Usuario(
            username="admin",
            email="admin@park.com",
            senha_hash=hash_senha("admin123"),
            nome_completo="Administrador"
        )
        db.add(admin)
        db.commit()
        print("✅ Usuário admin criado (usuário: admin / senha: admin123)")