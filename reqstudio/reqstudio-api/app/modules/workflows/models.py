"""Workflow, WorkflowStep and Agent models — global platform data (Story 5.1).

These models do NOT use TenantMixin. They represent system-wide
configuration (BMAD elicitation recipes) that is read-only in V1
and potentially editable via UI in V2.

Seed data is populated via Alembic migration.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Agent(Base):
    """Agente BMAD com system prompt específico.

    Exemplos: analyst (Mary), architect (Winston), pm (John).
    """

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)


class Workflow(Base):
    """Receita de elicitação (ex: briefing, PRD).

    config armazena metadados extras em JSON (ex: max_iterations, phase_type).
    """

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="workflow",
        order_by="WorkflowStep.position",
        cascade="all, delete-orphan",
    )


class WorkflowStep(Base):
    """Etapa individual de um workflow de elicitação.

    Cada step é executado por um Agent específico e contém
    o template de prompt que será usado pelo Context Builder.
    """

    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False,
    )
    agent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agents.id"), nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="elicitation",
    )

    workflow: Mapped["Workflow"] = relationship(back_populates="steps")
    agent: Mapped["Agent"] = relationship()
