from sqlalchemy.orm import Session
from domain.models.company_models import CompanyCreate
from domain.entities.company_entity import Company
from sqlalchemy import select, update

class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def register(self, company: CompanyCreate):

        company_entity = Company(
            customer_name=company.customer_name,
            company_name=company.company_name,
            phone_number=company.phone_number,
            address=company.address,
            contract_start_date=company.contract_start_date,
            contract_end_date=company.contract_end_date,
            cnae_company=company.cnae_company,
            tax_regime=company.tax_regime,
            erp_code=company.erp_code,
            monthly_value=company.monthly_value,
        )

        self.db.add(company_entity)
        self.db.commit()
        return company

    def find_all_company(self):
        query = select(Company)
        return self.db.execute(query).scalars().all()
