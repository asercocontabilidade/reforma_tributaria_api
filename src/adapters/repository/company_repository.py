from sqlalchemy.orm import Session
from domain.models.company_models import CompanyCreate, CompanyRead
from domain.entities.company_entity import Company
from domain.entities.user_entity import User
from sqlalchemy import select, update

class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def register(self, company: CompanyCreate):

        company_entity = Company(
            customer_name=company.customer_name,
            company_name=company.company_name,
            cnpj=company.cnpj,
            cpf=company.cpf,
            email=company.email,
            phone_number=company.phone_number,
            address=company.address,
            contract_start_date=company.contract_start_date,
            contract_end_date=company.contract_end_date,
            cnae_company=company.cnae_company,
            cnae_description=company.cnae_description,
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

    def find_company_by_company_id(self, company_id):
        query = select(Company).join(User).where(Company.id == company_id)
        return self.db.execute(query).scalars().first()

    def update_company(self, company: CompanyRead):
        query = update(Company).where(Company.id == company.id).values(
            customer_name=company.customer_name,
            role=company.role,
            company_name=company.company_name,
            cnpj=company.cnpj,
            cpf=company.cpf,
            email=company.email,
            phone_number=company.phone_number,
            address=company.address,
            contract_start_date=company.contract_start_date,
            contract_end_date=company.contract_end_date,
            cnae_company=company.cnae_company,
            cnae_description=company.cnae_description,
            tax_regime=company.tax_regime,
            erp_code=company.erp_code,
            monthly_value=company.monthly_value,
        )
        self.db.execute(query)
        self.db.commit()
        return company