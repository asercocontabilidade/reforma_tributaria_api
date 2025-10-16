# models.py
from sqlalchemy import String, Enum as SAEnum, Boolean, DateTime, func, inspect
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum as PyEnum
from sqlalchemy import event
from infrastructure.database import Base

class RoleType(str, PyEnum):
    administrator = "administrator"
    client = "client"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    cnpj_cpf: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(255), unique=False, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[RoleType] = mapped_column(
        SAEnum(RoleType, name="roletype"), nullable=False, default=RoleType.client
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_authenticated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


@event.listens_for(User, "before_update")
def update_status_changed_at(mapper, connection, target: User):
    """Atualiza status_changed_at apenas se o is_active for alterado."""
    state = inspect(target)
    hist = state.attrs.is_active.history

    if hist.has_changes():  # só se o valor realmente mudou
        target.status_changed_at = datetime.utcnow()