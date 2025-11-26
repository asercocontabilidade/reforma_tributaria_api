from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import time

router = APIRouter()

LOGIN_URL = "https://gbrasil.ip2apps.com.br/api/v1/auths/signin"
CHAT_URL  = "https://gbrasil.ip2apps.com.br/api/v1/chat/completions"

EMAIL = "ia@aserco.com.br"
PASSWORD = "Aserco32919100"

MODEL = "rt-25"

_cached_token = None
_token_expire = 0


async def login_rt25():
    global _cached_token, _token_expire

    if _cached_token and time.time() < _token_expire:
        return _cached_token

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(LOGIN_URL, json={
            "email": EMAIL,
            "password": PASSWORD
        })

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Falha ao autenticar RT25")

    token = resp.json().get("token")
    if not token:
        raise HTTPException(status_code=500, detail="Token ausente no login RT25")

    _cached_token = token
    _token_expire = time.time() + (30 * 60)

    return token


class ChatPayload(BaseModel):
    message: str
    max_tokens: int = 500
    temperature: float = 0.7


@router.post("/rt25/chat")
async def chat_rt25(payload: ChatPayload):
    token = await login_rt25()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": payload.message}
        ],
        "temperature": payload.temperature,
        "max_tokens": payload.max_tokens
    }

    async with httpx.AsyncClient(timeout=40) as client:
        resp = await client.post(CHAT_URL, json=body, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    data = resp.json()

    # pegar apenas o texto
    try:
        reply = data["choices"][0]["message"]["content"]
    except:
        reply = "⚠ Erro: resposta inesperada do modelo."

    # retorna somente o texto — igual ao ChatGPT
    return reply










