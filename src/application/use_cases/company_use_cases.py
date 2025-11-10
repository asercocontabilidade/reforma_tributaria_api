from sqlalchemy.orm import Session
from adapters.repository.company_repository import CompanyRepository
from domain.models.company_models import CompanyCreate, CompanyRead

class CompanyUseCases:

    def __init__(self, db: Session):
        self.repo = CompanyRepository(db)

    def register(self, company: CompanyCreate):
        return self.repo.register(company)

    def find_all_company(self):
        return self.repo.find_all_company()

    def find_company_by_company_id(self, company_id):
        return self.repo.find_company_by_company_id(company_id)

    def update_company(self, company: CompanyRead):
        return self.repo.update_company(company)