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
        rows = await conn.fetch("SELECT id, segment_index, video_name, description FROM video_scenes_v4 WHERE id != 'init'")
        print("--- Table Content ---")
        for r in rows:
            print(f"Seg={r['segment_index']} | {r['video_name']} | {r['description'][:50]}...")
        await conn.close()
    except Exception as e:
        print(f"Crash: {e}")

asyncio.run(run())
