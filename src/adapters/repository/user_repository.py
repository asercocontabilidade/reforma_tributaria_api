from datetime import datetime
from sqlalchemy.orm import Session
from domain.entities.user_entity import User
from domain.entities.code_entity import Code
from sqlalchemy import select, update
from application.use_cases.security import hash_password
import secrets

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def update_status(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        user.status_changed_at = datetime.utcnow()
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_status_is_authenticated(self, user: User, is_authenticated: bool) -> User:
        user.is_authenticated = is_authenticated
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_status_is_authenticated(self, email: str):
        query = select(User.is_authenticated).where(User.email == email)
        return self.db.execute(query).scalar()

    def find_all_users(self):
        query = select(User)
        return self.db.execute(query).scalars().all()

    def update_user_company(self, company_id, user_id):
        query = update(User).where(User.id == user_id).values(company_id=company_id)
        print("teste")
        self.db.execute(query)
        self.db.commit()

    def update_user_config(self, user_config):
        query = update(User).where(User.id == user_config.id).values(hashed_password=hash_password(user_config.password), full_name=user_config.full_name)
        self.db.execute(query)
        self.db.commit()

    def get_user_by_id(self, user_id):
        query = select(User).where(User.id == user_id)
        return self.db.execute(query).scalar()

    from sqlalchemy import update, select

    def update_user(self, user_update):
        query = (
            update(User)
            .where(User.id == user_update.id)
            .values(
                email=user_update.email,
                full_name=user_update.full_name,
                cnpj_cpf=user_update.cnpj_cpf,
                role=user_update.role,
            )
        )

        result = self.db.execute(query)
        self.db.commit()

        if result.rowcount == 0:
            return None  # não encontrou o id

        # Buscar o registro atualizado
        user = self.db.execute(
            select(User).where(User.id == user_update.id)
        ).scalar_one()
        return user

    def update_password(self, user_id: int, hashed_password: str):
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.password_hash = hashed_password
        self.db.commit()
        return True

    def get_user_code(self):
        MAX_ATTEMPTS = 10

        for _ in range(MAX_ATTEMPTS):
            number = secrets.randbelow(9000) + 1000

            stmt = select(Code).where(Code.code == number)
            code_obj = self.db.execute(stmt).scalar_one_or_none()

            if code_obj is None:
                new_code = Code(
                    code=number,
                    is_code_used=False
                )
                self.db.add(new_code)
                self.db.commit()
                self.db.refresh(new_code)
                return new_code.code

            if not code_obj.is_code_used:
                return code_obj.code

        raise RuntimeError("Não foi possível gerar um código válido")

    def validate_user_code(self, code):
        stmt = select(Code).where(Code.code == code)
        code_obj = self.db.execute(stmt).scalar_one_or_none()

        if code_obj is None:
            return {
                "success": False,
                "message": "Código inválido"
            }

        if code_obj.is_code_used:
            return {
                "success": False,
                "message": "Código inválido"
            }

        return {
            "success": True,
            "message": "Código válido"
        }

    def attach_user_code(self, user_id, code):
        stmt = select(Code).where(Code.code == code)
        code_obj = self.db.execute(stmt).scalar_one_or_none()

        if code_obj is None:
            return {
                "success": False,
                "message": "Código inválido"
            }

        if code_obj.is_code_used:
            return {
                "success": False,
                "message": "Código inválido"
            }

        code_obj.user_id = user_id
        code_obj.is_code_used = True

        self.db.commit()

        return {
            "success": True,
            "message": "Código vinculado ao usuário com sucesso",
            "code": code_obj.code,
            "user_id": user_id
        }
