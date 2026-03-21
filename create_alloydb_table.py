import asyncio
import asyncpg

async def main():
    conn_str = "postgresql://postgres:DefaultSearch_1234@34.64.97.194:5432/postgres"
    
    print("🔌 Connecting to AlloyDB...")
    try:
        conn = await asyncpg.connect(conn_str, ssl="require", timeout=10)
    except Exception as e:
        print(f"❌ Connection Failed: {repr(e)}")
        return

    try:
        print("💡 Enabling pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        print("📋 Creating table video_scenes_v4 if not exists...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS video_scenes_v4 (
            id VARCHAR(255) PRIMARY KEY,
            segment_index INTEGER,
            start_time DOUBLE PRECISION,
            end_time DOUBLE PRECISION,
            video_name VARCHAR(255),
            embedding VECTOR(3072),
            description TEXT,
            text_embedding VECTOR(3072),
            url TEXT
        );
        """
        await conn.execute(create_table_sql)
        
        # print("🔍 Creating IVFFlat Index for visual embeddings...")
        # await conn.execute("CREATE INDEX IF NOT EXISTS idx_v_embedding ON video_scenes_v4 USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);")
        
        # print("🔍 Creating IVFFlat Index for text embeddings...")
        # await conn.execute("CREATE INDEX IF NOT EXISTS idx_t_embedding ON video_scenes_v4 USING ivfflat (text_embedding vector_cosine_ops) WITH (lists = 10);")
        
        print("🔍 Creating GIN Index for text FTS...")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_desc_ts ON video_scenes_v4 USING gin (to_tsvector('simple', description));")
        
        print("✅ DDL & Indexing completed successfully!")
        
    except Exception as e:
        print(f"❌ Execution Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
