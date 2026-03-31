"""Seed de workflow padrão de elicitação de briefing.

Roda via: docker compose exec api python -m app.seeds.seed_workflows
Re-seed: docker compose exec api python -m app.seeds.seed_workflows --force
"""

import asyncio
import logging
import sys

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.modules.workflows.models import Agent, Workflow, WorkflowStep

logger = logging.getLogger(__name__)


SEED_AGENT = {
    "name": "Mary",
    "role": "analyst",
    "system_prompt": (
        "Você é Mary, analista de requisitos. Conduza a elicitação de forma "
        "objetiva e empática. Seja concisa: perguntas curtas e diretas, "
        "respostas de no máximo 3 parágrafos. Fale em português do Brasil. "
        "Nunca chame o usuário de 'especialista' — use o nome dele."
    ),
}

SEED_WORKFLOW = {
    "name": "elicitation-briefing",
    "description": "Fluxo de elicitação de briefing inicial do projeto",
}

SEED_STEPS = [
    {
        "position": 1,
        "step_type": "elicitation",
        "prompt_template": (
            "Me conte em poucas frases: qual problema seu projeto resolve? "
            "Quem é afetado?"
        ),
    },
    {
        "position": 2,
        "step_type": "elicitation",
        "prompt_template": (
            "Quem são os usuários principais? Algum outro grupo é afetado?"
        ),
    },
    {
        "position": 3,
        "step_type": "elicitation",
        "prompt_template": (
            "Quais resultados de negócio você espera alcançar?"
        ),
    },
    {
        "position": 4,
        "step_type": "elicitation",
        "prompt_template": (
            "Descreva brevemente o processo atual e como imagina o futuro."
        ),
    },
    {
        "position": 5,
        "step_type": "elicitation",
        "prompt_template": (
            "Existe alguma restrição de segurança, compliance ou performance?"
        ),
    },
]


async def seed(force: bool = False):
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        existing = await db.scalar(
            select(Workflow).where(Workflow.name == SEED_WORKFLOW["name"])
        )

        if existing and not force:
            print(f"✅ Workflow '{SEED_WORKFLOW['name']}' already exists (id={existing.id}). Use --force to re-seed.")
            return

        if existing and force:
            # Delete cascade: steps will be deleted automatically
            await db.execute(
                delete(WorkflowStep).where(WorkflowStep.workflow_id == existing.id)
            )
            await db.delete(existing)
            # Delete agent by name
            old_agent = await db.scalar(select(Agent).where(Agent.name == SEED_AGENT["name"]))
            if old_agent:
                await db.delete(old_agent)
            await db.flush()
            print("🗑️  Old seed deleted.")

        # Create agent
        agent = Agent(**SEED_AGENT)
        db.add(agent)
        await db.flush()

        # Create workflow
        workflow = Workflow(**SEED_WORKFLOW)
        db.add(workflow)
        await db.flush()

        # Create steps
        for step_data in SEED_STEPS:
            step = WorkflowStep(
                workflow_id=workflow.id,
                agent_id=agent.id,
                **step_data,
            )
            db.add(step)

        await db.commit()
        print(f"🌱 Seeded workflow '{workflow.name}' with {len(SEED_STEPS)} steps (id={workflow.id})")


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(seed(force=force))
