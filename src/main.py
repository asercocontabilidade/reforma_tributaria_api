# main.py
from fastapi import FastAPI
from application.controllers.autentication_controller import router as auth_router
from application.controllers.user_controller import router as user_router
from application.controllers.ncm_controller import router as ncm_router
from application.controllers.company_controller import router as company_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API App Reforma Tributária", version="0.1.0")

origins = [
    "http://localhost:5173",
    "http://192.168.1.65:5173",
    "http://192.168.1.65:5174",
    "http://192.168.1.113:3005",
    "http://localhost:5003",
    # adicione outros hosts que usar
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(ncm_router)
app.include_router(company_router)

@app.get("/health")
def health():
    return {"status": "ok"}
