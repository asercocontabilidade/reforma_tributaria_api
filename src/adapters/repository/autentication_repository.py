# autentication_repository.py
from typing import Optional
from sqlalchemy.orm import Session
from domain.entities.user_entity import User as UserORM,RoleType
from domain.entities.user_classes import UserEntity
from application.use_cases.security import hash_password, verify_password

class AuthenticationRepository:
    """Data access for users/auth (SQLAlchemy implementation)."""

    def __init__(self, db: Session):
        self.db = db

    # Queries
    def get_user_by_cnpj_cpf(self, cnpj_cpf: str) -> Optional[UserORM]:
        return self.db.query(UserORM).filter(UserORM.cnpj_cpf == cnpj_cpf).first()

    def get_user_by_email(self, email: str) -> Optional[UserORM]:
        return self.db.query(UserORM).filter(UserORM.email == email).first()

    # Commands
    def create_user(self, *, email: str, cnpj_cpf: str, ip_address: str | None, password: str, full_name: str | None, role: RoleType, company_id: int | None) -> UserEntity:
        if self.get_user_by_email(email):
            raise ValueError("Email already registered")

        # if self.get_user_by_cnpj_cpf(cnpj_cpf):
        #     raise ValueError("CNPJ CPF already registered")

        user = UserORM(
            email=email,
            cnpj_cpf=cnpj_cpf,
            ip_address=ip_address,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
            company_id=company_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return UserEntity(
            id=user.id,
            email=user.email,
            cnpj_cpf=cnpj_cpf,
            ip_address=ip_address,
            full_name=user.full_name,
            role=role,
            is_active=user.is_active,
            company_id=user.company_id,
        )

    def verify_credentials(self, *, email: str, password: str) -> Optional[UserEntity]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return UserEntity(
            id=user.id,
            email=user.email,
            cnpj_cpf=user.cnpj_cpf,
            ip_address=user.ip_address,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            company_id=user.company_id,
        )
