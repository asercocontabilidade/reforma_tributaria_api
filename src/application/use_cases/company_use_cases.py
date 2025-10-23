from sqlalchemy.orm import Session
from adapters.repository.company_repository import CompanyRepository
from domain.models.company_models import CompanyCreate

class CompanyUseCases:

    def __init__(self, db: Session):
        self.repo = CompanyRepository(db)

    def register(self, company: CompanyCreate):
        return self.repo.register(company)

    def find_all_company(self):
        return self.repo.find_all_company()