import uuid
from enum import Enum

from app.db.base import Base
from sqlalchemy import ARRAY, Column, String
from sqlalchemy.dialects.postgresql import UUID


class Role(str, Enum):
    admin = "admin"
    student = "student"
    teacher = "teacher"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    password = Column(String, nullable=False)
    roles = Column(ARRAY(String), nullable=False, default=[])
