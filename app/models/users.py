import uuid

from app.db.base import Base
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class UsersRole(Base):
    __tablename__ = "users_role"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String, nullable=False, unique=True)

    users = relationship("User", secondary=UsersRole.__table__, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    lastname = Column(String, nullable=False)

    roles = relationship("Role", secondary=UsersRole.__table__, back_populates="users")
