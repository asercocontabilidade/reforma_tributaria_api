from typing import Tuple
from sqlalchemy.orm import Session
from domain.entities.user_classes import RoleType
from adapters.repository.autentication_repository import AuthenticationRepository
from adapters.repository.user_repository import UserRepository
from application.use_cases.security import create_access_token
from domain.entities.user_classes import UserEntity

class AuthenticationUseCases:
    """Application business rules for auth."""

    def __init__(self, db: Session):
        self.repo = AuthenticationRepository(db)
        self.repo_user = UserRepository(db)

    def register_user(
        self, *, email: str, cnpj_cpf: str, ip_address: str | None, password: str, full_name: str | None, role: RoleType
    ) -> UserEntity:
        return self.repo.create_user(email=email,cnpj_cpf=cnpj_cpf, ip_address=ip_address, password=password, full_name=full_name, role=role)

    def login(self, *, email: str, password: str) -> Tuple[str, UserEntity]:
        user = self.repo.verify_credentials(email=email, password=password)

        status_is_authenticated = self.repo_user.get_status_is_authenticated(email)
        print(status_is_authenticated)

        if not status_is_authenticated:
            user_auth = self.repo.get_user_by_email(email)
            self.repo_user.update_status_is_authenticated(user=user_auth, is_authenticated=True)

        if not user:
            raise ValueError("Credenciais Inválidas")

        if status_is_authenticated:
            raise ValueError("conta já está sendo utilizada")
        
        token = create_access_token(email=user.email, role=user.role)
        return token, user
