from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from adapters.repository.user_repository import UserRepository
from adapters.repository.contract_repository import ContractRepository

class UserUseCases:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.contract_repo = ContractRepository(db)

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

    def update_user_company(self, company_id, user_id):
        self.repo.update_user_company(company_id, user_id)

    def update_user_config(self, user_config):
        self.repo.update_user_config(user_config)

    def get_user_by_id(self, user_id):
        return self.repo.get_user_by_id(user_id)

    def update_user(self, user_update):
        return self.repo.update_user(user_update)

    def contract_signing(self, contract, ip_address_local):
        return self.contract_repo.contract_signing(contract, ip_address_local)

    def is_signed_contract(self, user_id, type_contract):
        return self.contract_repo.is_signed_contract(user_id, type_contract)

    def get_ramdom_int_number_user_code(self):
        return self.repo.get_user_code()

    def validate_user_code(self, code):
        return self.repo.validate_user_code(code)

    def attach_user_code(self, user_id, code):
        return self.repo.attach_user_code(user_id, code)