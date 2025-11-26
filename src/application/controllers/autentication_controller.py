# autentication_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from infrastructure.database import get_db
from domain.models.user_models import UserCreate, UserRead, LoginRequest, Token, LoginResponse, ForgotPasswordRequest, ResetPasswordRequest
from domain.entities.user_entity import RoleType
from domain.entities.user_classes import UserEntity
from application.use_cases.autentication_use_cases import AuthenticationUseCases
from application.use_cases.security import (
    get_current_user, require_roles,
    create_access_token, create_refresh_token, decode_token
)
from application.utils.utils import get_client_ip
from domain.entities.user_entity import User
from infrastructure.security_docs import swagger_bearer_auth
import logging
from sqlalchemy.exc import IntegrityError, DataError

REFRESH_COOKIE_NAME = "rt"  # nome do cookie do refresh
REFRESH_COOKIE_PATH = "/auth"  # limite de escopo
REFRESH_COOKIE_SECURE = True  # mude para True em produção com HTTPS
REFRESH_COOKIE_SAMESITE = "Lax"

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)

def _dup_key_on(err: IntegrityError, needle: str) -> bool:
    """Detecta qual constraint/coluna disparou o 1062 do MySQL."""
    msg = str(getattr(err, "orig", err))
    return needle in msg

@router.post("/register", response_model=UserRead, status_code=201, summary="Search items (auth required)", dependencies=[swagger_bearer_auth()])
def register(payload: UserCreate,
             request: Request, db: Session = Depends(get_db),
             current: UserEntity = Depends(get_current_user)
             ):
    uc = AuthenticationUseCases(db)

    # ip_address_local = get_client_ip(request)
    ip_address_local = payload.ip_address

    """
    existing = db.query(User).filter(User.ip_address == ip_address_local).first()

    if existing:
        # 409: já existe; retorno claro
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="IP já cadastrado para outro usuário."
        )
    """

    try:
        # saneamento básico: não grave o literal "string"
        if isinstance(ip_address_local, str) and ip_address_local.strip().lower() == "string":
            if ip_address_local is None:
                ip_address_local = None

        user = uc.register_user(
            email=payload.email,
            cnpj_cpf=payload.cnpj_cpf,
            ip_address=ip_address_local,
            password=payload.password,
            full_name=payload.full_name,
            role=RoleType(payload.role),  # pode lançar ValueError se role inválido
            company_id=payload.company_id,  # pode ser None
        )

        return UserRead(
            id=user.id,
            email=user.email,
            cnpj_cpf=user.cnpj_cpf,
            ip_address=user.ip_address,  # preferir o valor vindo do ORM
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            company_id=user.company_id,
        )

    except IntegrityError as e:
        # Se você controlar a sessão aqui, lembre de dar rollback:
        # db.rollback()

        # 1062 (duplicado) em chaves comuns
        if _dup_key_on(e, "uq_users_ip_address") or _dup_key_on(e, "ip_address"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"field": "ip_address", "msg": "Endereço IP já cadastrado."},
            )
        if _dup_key_on(e, "uq_users_email") or _dup_key_on(e, "email"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"field": "email", "msg": "E-mail já cadastrado."},
            )
        if _dup_key_on(e, "uq_users_cnpj_cpf") or _dup_key_on(e, "cnpj_cpf"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"field": "cnpj_cpf", "msg": "CNPJ/CPF já cadastrado."},
            )

        logger.exception("Integrity error ao registrar usuário")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Violação de integridade nos dados informados."
        )

    except ValueError as e:
        # pega, por exemplo, RoleType(payload.role) inválido
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except DataError as e:
        # erros de tamanho de campo, tipos numéricos fora do range etc.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dados inválidos para um dos campos.")

    except Exception as e:
        logger.exception("Falha inesperada ao registrar usuário")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro interno do servidor.")

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

@router.post("/refresh")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    rt = request.cookies.get(REFRESH_COOKIE_NAME)
    if not rt:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    data = decode_token(rt)  # valida exp/assinatura; lança 401 se inválido/expirado
    user: User | None = db.query(User).filter(User.email == data.sub).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # (opcional) você pode rotacionar o refresh aqui emitindo um novo cookie
    at = create_access_token(email=user.email, role=user.role)
    return {"access_token": at, "token_type": "bearer"}


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

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest,
                    db: Session = Depends(get_db),
                    current: UserEntity = Depends(get_current_user)
                    ):
    uc = AuthenticationUseCases(db)

    try:
        uc.forgot_password(email=payload.email)
        return {"message": "Se o e-mail existir no sistema, enviaremos instruções de redefinição."}
    except Exception:
        # Nunca revelar se o email existe ou não!
        return {"message": "Se o e-mail existir no sistema, enviaremos instruções de redefinição."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest,
                   db: Session = Depends(get_db),
                   current: UserEntity = Depends(get_current_user)
                   ):
    uc = AuthenticationUseCases(db)

    try:
        uc.reset_password(token=payload.token, new_password=payload.new_password)
        return {"message": "Senha redefinida com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

