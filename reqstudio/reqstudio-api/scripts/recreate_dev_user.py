"""Recreate dev user for local development.

Usage:
    python scripts/recreate_dev_user.py [--email EMAIL] [--password PASSWORD]

Credentials can also be set via environment variables:
    DEV_USER_EMAIL    (default: admin@reqstudio.com)
    DEV_USER_PASSWORD (required — no hardcoded default)
"""

import argparse
import asyncio
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório atual ao sys.path para importar app
sys.path.append(os.getcwd())

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.modules.auth.models import Tenant, User  # noqa: E402

DEFAULT_EMAIL = "admin@reqstudio.com"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recreate dev user")
    parser.add_argument(
        "--email",
        default=os.environ.get("DEV_USER_EMAIL", DEFAULT_EMAIL),
        help="Dev user email (env: DEV_USER_EMAIL)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("DEV_USER_PASSWORD"),
        help="Dev user password (env: DEV_USER_PASSWORD)",
    )
    return parser.parse_args()


async def recreate_dev_user(email: str, password: str) -> None:
    print("--- ReqStudio Recovery ---")
    print(f"Database: {settings.DATABASE_URL}")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Garantir Tenant
        result = await session.execute(select(Tenant).where(Tenant.name == "Dev Tenant"))
        tenant = result.scalar_one_or_none()

        if not tenant:
            print("Criando Dev Tenant...")
            tenant = Tenant(name="Dev Tenant")
            session.add(tenant)
            await session.flush()
        else:
            print(f"Tenant encontrado: {tenant.id}")

        # 2. Garantir Usuário
        hashed = hash_password(password)

        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            print(f"Usuário {email} já existe. Atualizando senha...")
            user.hashed_password = hashed
            user.tenant_id = tenant.id
        else:
            print(f"Criando usuário {email}...")
            user = User(email=email, hashed_password=hashed, tenant_id=tenant.id)
            session.add(user)

        await session.commit()
        print("\nACESSO RECUPERADO!")
        print(f"Email: {email}")
        print(f"Tenant ID: {tenant.id}")
        print("---------------------------")


if __name__ == "__main__":
    args = _parse_args()
    if not args.password:
        print(
            "ERROR: Password is required. "
            "Pass --password or set DEV_USER_PASSWORD env var.",
            file=sys.stderr,
        )
        sys.exit(1)
    asyncio.run(recreate_dev_user(args.email, args.password))
