from datetime import datetime
from sqlalchemy.orm import Session
from domain.entities.user_entity import User
from sqlalchemy import select, update
from application.use_cases.security import hash_password

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
