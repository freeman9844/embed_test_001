import asyncpg
import asyncio

async def run():
    try:
        conn = await asyncpg.connect('postgresql://postgres:DefaultSearch_1234@34.64.97.194:5432/postgres', ssl='require')
        rows = await conn.fetch("SELECT id, segment_index, video_name, description FROM video_scenes_v4 WHERE id != 'init'")
        print("--- Table Content ---")
        for r in rows:
            print(f"Seg={r['segment_index']} | {r['video_name']} | {r['description'][:50]}...")
        await conn.close()
    except Exception as e:
        print(f"Crash: {e}")

asyncio.run(run())
