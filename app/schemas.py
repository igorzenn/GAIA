from pydantic import BaseModel, Field # Usado para validar a estrutura dos dados
from typing import Literal, Any # Foi usado para definir um conjunto especifico 

class GaiaRequest(BaseModel): # Classe de requisição, gaiarequest herda de basemodel
    mensagem_usuario: str = Field(..., min_lenght=1) # Define que a essa opção so pode ser uma string, (...) obrigatoriamente preenchida e (min_lenght) mostra que tem q ter no min um caracter
    sessionId: str = Field(..., min_lenght=1)
    executionMode: str | None = "production" # Caso executionmode não venha será definido como production

class GaiaResponse(BaseModel): # Como o cod vai mandar os dados pro N8N 
    agent: str
    response: str
    sessionId: str
    status: Literal["success", "error"] = "success"  # O literal serve para poder usar um conjunto de dados
    metadata: dict[str, Any] | None = None

class AgentResult(BaseModel): # Resposta interna de cada agente 
    response: str
    intent: str | None = None 
    data: dict[str, Any] | None = None

class RouterResult(BaseModel):
    agent: str
    intent: str