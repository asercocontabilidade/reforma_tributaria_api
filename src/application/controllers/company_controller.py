from fastapi import APIRouter, Depends, HTTPException, status, Request
from infrastructure.database import get_db
from sqlalchemy.orm import Session
from domain.models.company_models import CompanyCreate, CompanyRead
from application.use_cases.company_use_cases import CompanyUseCases
from domain.entities.user_classes import UserEntity
from application.use_cases.security import (
    get_current_user, require_roles)
from typing import List

router = APIRouter(prefix="/company", tags=["company"])

@router.post("/register", status_code=201, summary="Search items (auth required)", response_model=CompanyCreate)
def register_customer(payload: CompanyCreate,db: Session = Depends(get_db), current: UserEntity = Depends(get_current_user)):
    uc = CompanyUseCases(db)
    return uc.register(payload)

@router.get("/find_all_company", response_model=List[CompanyRead])
def find_all_company(db: Session = Depends(get_db),
                     current: UserEntity = Depends(get_current_user)
                     ):
    uc = CompanyUseCases(db)
    return uc.find_all_company()

@router.get("/find_company_by_company_id/{company_id}", response_model=CompanyRead)
def find_company_by_company_id(
        company_id: int,
        db: Session = Depends(get_db),
        current: UserEntity = Depends(get_current_user)
):
    uc = CompanyUseCases(db)
    return uc.find_company_by_company_id(company_id)
