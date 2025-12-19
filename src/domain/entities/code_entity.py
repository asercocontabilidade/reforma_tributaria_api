from infrastructure.database import Base
from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, relationship


class Code(Base):
    __tablename__ = 'code'
    id: Mapped[int] = Column(Integer, primary_key=True)
    code = Column(Integer)
    is_code_used = Column(Boolean)

    user_id: Mapped[int] = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        unique=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="code",
        uselist=False
    )