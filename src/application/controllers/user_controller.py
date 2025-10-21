from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from domain.models.user_models import UserRead
from application.use_cases.user_use_cases import UserUseCases
from domain.entities.user_entity import RoleType
from application.use_cases.security import require_roles
from typing import List
from application.use_cases.security import (
    get_current_user, require_roles,
)
from domain.entities.user_classes import UserEntity

router = APIRouter(prefix="/users", tags=["users"])

@router.patch("/{user_id}/status", response_model=UserRead)
def change_user_status(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current: UserEntity = Depends(get_current_user),
    # _: None = Depends(require_roles(RoleType.administrator)),  # Apenas admin pode alterar
):
    """
    Atualiza o status (ativo/inativo) de um usuário.
    Corpo esperado: {"is_active": true/false}
    """
    if "is_active" not in payload:
        raise HTTPException(status_code=400, detail="Missing field 'is_active'")

    use_case = UserUseCases(db)
    user = use_case.change_user_status(user_id=user_id, is_active=payload["is_active"])
    return user

@router.patch("/{user_id}/authenticated_status", response_model=UserRead)
def change_user_status(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    # _: None = Depends(require_roles(RoleType.administrator)),  # Apenas admin pode alterar
):
    """
    Atualiza o status (ativo/inativo) de um usuário.
    Corpo esperado: {"is_authenticated": true/false}
    """
    if "is_authenticated" not in payload:
        raise HTTPException(status_code=400, detail="Missing field 'is_authenticated'")

    use_case = UserUseCases(db)
    user = use_case.change_user_is_authenticated_status(user_id=user_id, is_authenticated=payload["is_authenticated"])
    return user

@router.get("/find_all_users", response_model=List[UserRead])
def find_all_users(db: Session = Depends(get_db), current: UserEntity = Depends(get_current_user)):
    use_case = UserUseCases(db)

    return use_case.find_all_users()