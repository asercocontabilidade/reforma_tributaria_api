from infrastructure.database import Base
from sqlalchemy import Column, Integer, Float, Boolean, String, inspect, DateTime, ForeignKey,Enum as SAEnum
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)
from typing import Optional
from zoneinfo import ZoneInfo
from sqlalchemy import event
from datetime import datetime

BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")

class Contract(Base):
    __tablename__ = 'contract'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type_of_contract: Mapped[str | None] = Column(String(255), nullable=False)
    date_time_accepted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_signature_accepted: Mapped[bool] = Column(Boolean, nullable=True)
    term_content: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(255), unique=False, index=True, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="contracts")

@event.listens_for(Contract, "before_insert")
def set_date_on_create(mapper, connection, target: Contract):
    """Define date_time_accepted ao criar o contrato,
    somente se is_signature_accepted vier como True."""

    if target.is_signature_accepted:
        target.date_time_accepted = datetime.now(BRAZIL_TZ)