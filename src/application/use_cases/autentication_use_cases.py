from typing import Tuple
from sqlalchemy.orm import Session
from domain.entities.user_classes import RoleType
from adapters.repository.autentication_repository import AuthenticationRepository
from adapters.repository.user_repository import UserRepository
from application.use_cases.security import create_access_token, verify_password, hash_password, decode_token
from domain.entities.user_classes import UserEntity
from application.utils.email_service import send_email_html, reset_password_template, FRONTEND_RESET_URL

class AuthenticationUseCases:
    """Application business rules for auth."""

    def __init__(self, db: Session):
        self.repo = AuthenticationRepository(db)
        self.repo_user = UserRepository(db)

    def register_user(
        self, *, email: str, cnpj_cpf: str, ip_address: str | None, password: str, full_name: str | None, role: RoleType, company_id: int | None
    ) -> UserEntity:
        return self.repo.create_user(email=email,cnpj_cpf=cnpj_cpf, ip_address=ip_address, password=password, full_name=full_name, role=role, company_id=company_id)

    def login(self, *, email: str, password: str) -> Tuple[str, UserEntity]:
        user = self.repo.verify_credentials(email=email, password=password)

        status_is_authenticated = self.repo_user.get_status_is_authenticated(email)
        print(status_is_authenticated)

        if not user:
            raise ValueError("Credenciais Inválidas")

        if not status_is_authenticated:
            user_auth = self.repo.get_user_by_email(email)
            self.repo_user.update_status_is_authenticated(user=user_auth, is_authenticated=True)

        if status_is_authenticated:
            raise ValueError("conta já está sendo utilizada")

        token = create_access_token(email=user.email, role=user.role)
        return token, user

    def forgot_password(self, email: str):
        user = self.repo_user.get_user_by_email(email)
        if not user:
            return

        reset_token = create_access_token(
            email=user.email,
            role=user.role,
            expires_minutes=15
        )

        # Monta URL real do botão no email
        reset_url = f"{FRONTEND_RESET_URL}?token={reset_token}"

        html = reset_password_template(
            reset_url=reset_url,
            user_name=user.full_name
        )

        # Envia e-mail real
        send_email_html(
            to_email=user.email,
            subject="Redefinição de Senha - Aserco Sistemas",
            html_content=html
        )

    def reset_password(self, token: str, new_password: str):
        try:
            data = decode_token(token)
        except Exception:
            raise ValueError("Token inválido ou expirado")

        user = self.repo_user.get_user_by_email(data.sub)
        if not user:
            raise ValueError("Token inválido")

        hashed = hash_password(new_password)
        self.repo_user.update_password(user.id, hashed)

        # Opcional: deslogar sessões anteriores
        self.repo_user.update_status_is_authenticated(user, False)

