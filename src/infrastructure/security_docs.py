# infrastructure/security_docs.py
from fastapi import Depends
from application.use_cases.security import http_bearer

def swagger_bearer_auth():
    # Apenas registra o esquema Bearer na UI; não valida nada.
    return Depends(http_bearer)
