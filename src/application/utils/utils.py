# utils.py
from fastapi import Request

def get_client_ip(request: Request) -> str:
    """Tenta extrair IP real atrás de proxy/load balancer."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # Pega o primeiro IP da cadeia
        return xff.split(",")[0].strip()
    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip()
    return request.client.host if request.client else "0.0.0.0"
