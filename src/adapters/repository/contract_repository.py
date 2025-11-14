from sqlalchemy.orm import Session
from domain.models.contract_models import ContractCreate
from domain.entities.contract_entity import Contract
from sqlalchemy import and_
from fastapi import HTTPException


class ContractRepository:
    def __init__(self, db: Session):
        self.db = db

    def contract_signing(self, contract: ContractCreate, ip_address_local):

        contract_entity = Contract(
            user_id=contract.user_id,
            type_of_contract=contract.type_of_contract,
            is_signature_accepted=contract.is_signature_accepted,
            term_content=contract.term_content,
            ip_address=ip_address_local,
        )

        self.db.add(contract_entity)
        self.db.commit()

    def is_signed_contract(self, user_id, type_contract):
        query = (
            self.db.query(Contract.is_signature_accepted)
            .filter(
                Contract.user_id == user_id,
                Contract.type_of_contract == type_contract
            )
        )

        row = query.first()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Contrato não encontrado para este usuário e tipo de contrato."
            )

        return row[0]