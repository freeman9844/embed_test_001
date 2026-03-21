import asyncpg
import asyncio

async def count():
    conn = await asyncpg.connect('postgresql://postgres:DefaultSearch_1234@34.64.97.194:5432/postgres', ssl='require')
    print('Rows:', await conn.fetchval('SELECT COUNT(*) FROM video_scenes_v4'))
    await conn.close()

asyncio.run(count())
