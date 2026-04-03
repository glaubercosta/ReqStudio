import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Adiciona o diretório atual ao sys.path para importar app
import os
sys.path.append(os.getcwd())

from app.core.config import settings
from app.core.security import hash_password
from app.modules.auth.models import User, Tenant

async def recreate_dev_user():
    print(f"--- ReqStudio Recovery ---")
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
        email = "admin@reqstudio.com"
        password = "admin123"
        hashed = hash_password(password)
        
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"Usuário {email} já existe. Atualizando senha...")
            user.hashed_password = hashed
            user.tenant_id = tenant.id
        else:
            print(f"Criando usuário {email}...")
            user = User(
                email=email,
                hashed_password=hashed,
                tenant_id=tenant.id
            )
            session.add(user)
            
        await session.commit()
        print(f"\n✅ ACESSO RECUPERADO!")
        print(f"Email: {email}")
        print(f"Senha: {password}")
        print(f"Tenant ID: {tenant.id}")
        print(f"---------------------------")

if __name__ == "__main__":
    asyncio.run(recreate_dev_user())
