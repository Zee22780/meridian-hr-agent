import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    department = Column(String)
    title = Column(String)
    hire_date = Column(DateTime)
    manager_id = Column(String)
    manager_email = Column(String)
    employment_type = Column(String)
    location = Column(String)
    benefits_tier = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    onboarding = relationship("OnboardingProgress", back_populates="employee", uselist=False)
    escalations = relationship("Escalation", back_populates="employee")
    agent_actions = relationship("AgentAction", back_populates="employee")


class OnboardingProgress(Base):
    __tablename__ = "onboarding_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    status = Column(String, nullable=False, default="in_progress")
    steps = Column(JSONB, nullable=False, default=dict)
    escalations = Column(JSONB, nullable=False, default=list)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    employee = relationship("Employee", back_populates="onboarding")


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="medium")
    reason = Column(Text, nullable=False)
    context = Column(JSONB, default=dict)
    assigned_to = Column(String)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)
    resolution = Column(Text)

    employee = relationship("Employee", back_populates="escalations")


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String)
    source_file = Column(String)
    embedding = Column(Vector(1536))
    version = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True)
    input = Column(JSONB)
    output = Column(JSONB)
    timestamp = Column(DateTime, server_default=func.now())
    status = Column(String, nullable=False, default="success")
    error = Column(Text)

    employee = relationship("Employee", back_populates="agent_actions")
