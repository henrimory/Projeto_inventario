from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ComputadorBase(BaseModel):
    patrimonio: str
    nome: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    processador: Optional[str] = None
    memoria_ram: Optional[str] = None
    armazenamento: Optional[str] = None
    status: str = "Disponivel"
    localizacao: Optional[str] = None
    usuario_responsavel: Optional[str] = None

class ComputadorCreate(ComputadorBase):
    pass

class ComputadorUpdate(BaseModel):
    patrimonio: Optional[str] = None
    nome: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    processador: Optional[str] = None
    memoria_ram: Optional[str] = None
    armazenamento: Optional[str] = None
    status: Optional[str] = None
    localizacao: Optional[str] = None
    usuario_responsavel: Optional[str] = None
    ativo: Optional[bool] = None

class ComputadorResponse(ComputadorBase):
    id: int
    ativo: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
