from infrastructure.database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey,Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from typing import List, Optional

class RoleType(str, PyEnum):
    basic = "basic"
    pro = "pro"
    special = "special"

class Company(Base):
    __tablename__ = 'company'

    id = Column(Integer, primary_key=True)
    customer_name: Mapped[str | None] = Column(String(255), nullable=True)
    role: Mapped[RoleType] = mapped_column(
        SAEnum(RoleType, name="roletype"), nullable=False, default=RoleType.basic
    )
    company_name: Mapped[str | None] = Column(String(255), nullable=True)
    cnpj: Mapped[str | None] = Column(String(255), nullable=False)
    phone_number: Mapped[str | None] = Column(String(255), nullable=True)
    address: Mapped[str | None] = Column(String(255), nullable=True)
    contract_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    contract_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cnae_company: Mapped[str | None] = Column(String(255), nullable=True)
    tax_regime: Mapped[str | None] = Column(String(255), nullable=True)
    erp_code: Mapped[str | None] = Column(String(50), nullable=True)
    monthly_value: Mapped[float | None] = Column(Float, nullable=True)


    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    users: Mapped[List["Users"]] = relationship(
        "User", back_populates="company", cascade="save-update, merge", passive_deletes=True
    )
