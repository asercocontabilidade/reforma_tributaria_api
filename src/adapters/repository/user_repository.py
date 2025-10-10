from datetime import datetime
from sqlalchemy.orm import Session
from domain.entities.user_entity import User
from sqlalchemy import select

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
