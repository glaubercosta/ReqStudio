"""Diagnostic script for ReqStudio Backend.

Checks DB connectivity, tables and basic health.
Run via: docker compose exec api python scripts/rescue.py
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Adiciona o diretório app ao path se necessário
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def check_health():
    print("--- ReqStudio Rescue Check ---")
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL not found in environment!")
        return

    print(f"🔍 Testing connection to: {db_url.split('@')[-1]}")
    
    try:
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            # 1. Test Select 1
            await conn.execute(text("SELECT 1"))
            print("✅ DB Connection: OK")
            
            # 2. Check Tables
            tables = ["users", "tenants", "projects", "sessions", "artifacts"]
            print("🔍 Checking essential tables...")
            for table in tables:
                try:
                    await conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    print(f"   - {table}: OK")
                except Exception:
                    print(f"   - {table}: ❌ NOT FOUND (or empty/error)")
            
            # 3. Check User count
            res = await conn.execute(text("SELECT count(*) FROM users"))
            count = res.scalar()
            print(f"👤 Total Users registered: {count}")
            
    except Exception as e:
        print(f"❌ DATABASE ERROR: {str(e)}")
    finally:
        print("--- End of Check ---")

if __name__ == "__main__":
    asyncio.run(check_health())
