import asyncpg
import asyncio

async def run():
    conn = await asyncpg.connect('postgresql://postgres:DefaultSearch_1234@34.64.97.194:5432/postgres', ssl='require')
    row = await conn.fetch("SELECT name, default_version FROM pg_available_extensions WHERE name = 'pg_bigm'")
    print("pg_bigm availability:", row)
    await conn.close()

asyncio.run(run())
