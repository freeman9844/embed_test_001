import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    try:
        host = os.getenv("DB_HOST", "localhost")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "postgres")
        
        conn_str = f"postgresql://{user}:{password}@{host}:5432/{database}"
        conn = await asyncpg.connect(conn_str, ssl='require')
        
        print("Enabling pg_bigm extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_bigm")
        
        print("Creating GIN bigm_ops Index on description...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_description_bigm ON video_scenes_v4 USING gin (description gin_bigm_ops)")
        
        print("✅ pg_bigm setup successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Error setting up pg_bigm: {e}")

asyncio.run(run())
