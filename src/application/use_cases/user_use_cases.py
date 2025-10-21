from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from adapters.repository.user_repository import UserRepository

class UserUseCases:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def change_user_status(self, user_id: int, is_active: bool):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        updated = self.repo.update_status(user, is_active)
        return updated

    def change_user_is_authenticated_status(self, user_id: int, is_authenticated: bool):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        updated = self.repo.update_status_is_authenticated(user, is_authenticated)
        return updated

    def find_all_users(self):
        return self.repo.find_all_users()
