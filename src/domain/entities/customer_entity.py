from infrastructure.database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey,Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from domain.entities.user_entity import User
from enum import Enum as PyEnum

class RoleType(str, PyEnum):
    basic = "basic"
    pro = "pro"

class Customer(Base):
    __tablename__ = 'customer'

    id = Column(Integer, primary_key=True)
    name: Mapped[str | None] = Column(String(255), nullable=True)
    role: Mapped[RoleType] = mapped_column(
        SAEnum(RoleType, name="roletype"), nullable=False, default=RoleType.basic
    )
    company_name: Mapped[str | None] = Column(String(255), nullable=True)
    phone_number: Mapped[str | None] = Column(String(255), nullable=True)
    address: Mapped[str | None] = Column(String(255), nullable=True)
    contract_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    contract_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cnae_company: Mapped[str | None] = Column(String(255), nullable=True)
    tax_regime: Mapped[str | None] = Column(String(255), nullable=True)
    erp_code: Mapped[str | None] = Column(String(50), nullable=True)

    user_id: Mapped[int] = Column(Integer, ForeignKey('user.id'), nullable=True)
    user = relationship(User)
