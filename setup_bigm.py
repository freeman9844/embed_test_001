import asyncpg
import asyncio

async def run():
    try:
        conn = await asyncpg.connect('postgresql://postgres:DefaultSearch_1234@34.64.97.194:5432/postgres', ssl='require')
        
        print("Enabling pg_bigm extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_bigm")
        
        print("Creating GIN bigm_ops Index on description...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_description_bigm ON video_scenes_v4 USING gin (description gin_bigm_ops)")
        
        print("✅ pg_bigm setup successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Error setting up pg_bigm: {e}")

asyncio.run(run())
