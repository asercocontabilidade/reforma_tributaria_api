# autentication_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from infrastructure.database import get_db
from domain.models.user_models import UserCreate, UserRead, LoginRequest, Token, LoginResponse
from domain.entities.user_entity import RoleType
from domain.entities.user_classes import UserEntity
from application.use_cases.autentication_use_cases import AuthenticationUseCases
from application.use_cases.security import get_current_user, require_roles
from application.utils.utils import get_client_ip
from domain.entities.user_entity import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate,request: Request, db: Session = Depends(get_db)):
    uc = AuthenticationUseCases(db)

    # ip_address_local = get_client_ip(request)
    # existing = db.query(User).filter(User.ip_address == ip_address_local).first()

    ip_address_local = payload.ip_address
    existing = db.query(User).filter(User.ip_address == ip_address_local).first()

    if existing:
        # 409: já existe; retorno claro
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="IP já cadastrado para outro usuário."
        )

    try:

        if ip_address_local is None:
            ip_address_local = None

        user = uc.register_user(
            email=payload.email,
            cnpj_cpf=payload.cnpj_cpf,
            ip_address=ip_address_local,
            password=payload.password,
            full_name=payload.full_name,
            role=RoleType(payload.role),
        )

        return UserRead(
            id=user.id,
            email=user.email,
            cnpj_cpf=user.cnpj_cpf,
            ip_address=ip_address_local,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    uc = AuthenticationUseCases(db)
    try:
        token, user = uc.login(email=payload.email, password=payload.password)
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role.value,
            "is_active": user.is_active,
            "id": user.id,
        }
    except ValueError as e:
        msg = str(e)
        if msg == "conta já está sendo utilizada":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conta já está sendo utilizada no momento."
            )
        elif msg == "Credenciais Inválidas":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais Inválidas."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg
            )

@router.get("/me", response_model=UserRead)
def me(current: UserEntity = Depends(get_current_user)):
    return UserRead(
        id=current.id,
        email=current.email,
        full_name=current.full_name,
        role=current.role.value,
        is_active=current.is_active,
    )

# Example of RBAC-protected route:
@router.get("/admin-only", response_model=dict)
def admin_only(_: UserEntity = Depends(require_roles(RoleType.administrator))):
    return {"message": "You are an administrator."}
