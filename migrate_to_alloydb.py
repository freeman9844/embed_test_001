import asyncio
import asyncpg
import lancedb
import numpy as np

def vector_to_str(vec):
    """Converts a vector (list or np.array) into pgvector string format '[1.0, 2.0]'"""
    if vec is None:
         return None
    if isinstance(vec, np.ndarray):
         vec = vec.tolist()
    return f"[{','.join(map(str, vec))}]"

async def main():
    # 1. Connect to LanceDB
    DB_PATH = "app/database/lancedb"
    print(f"📂 Connecting to LanceDB at {DB_PATH}...")
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table("video_scenes_v4")
    except Exception as e:
        print(f"❌ LanceDB Connection Failed: {e}")
        return

    # 2. Connect to AlloyDB
    conn_str = "postgresql://postgres:DefaultSearch_1234@34.64.97.194:5432/postgres"
    print("🔌 Connecting to AlloyDB...")
    try:
        conn = await asyncpg.connect(conn_str, ssl="require", timeout=10)
    except Exception as e:
        print(f"❌ AlloyDB Connection Failed: {repr(e)}")
        return

    try:
        # 3. Read Rows from LanceDB
        print("📥 Loading rows from LanceDB...")
        rows = table.search().to_list()
        total_rows = len(rows)
        print(f"📦 Found {total_rows} rows in LanceDB.")
        
        if total_rows == 0:
            print("💡 No rows to migrate.")
            return

        # 4. Prepare Inserting List of tuples
        print("⏳ Preparing records for Insertion...")
        records = []
        for row in rows:
            id_val = str(row['id'])
            segment_index = int(row['segment_index'])
            start_time = float(row['start_time'])
            end_time = float(row['end_time'])
            video_name = str(row['video_name'])
            description = str(row['description'])
            url = str(row['url'])
            
            emb_str = vector_to_str(row['embedding'])
            text_emb_str = vector_to_str(row['text_embedding'])
            
            records.append((
                id_val, segment_index, start_time, end_time, 
                video_name, emb_str, description, text_emb_str, url
            ))

        # 5. Insert records
        print("📤 Inserting records into AlloyDB (video_scenes_v4)...")
        # Using string representation casts to vector datatype perfectly node
        insert_sql = """
        INSERT INTO video_scenes_v4 (id, segment_index, start_time, end_time, video_name, embedding, description, text_embedding, url)
        VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8::vector, $9)
        ON CONFLICT (id) DO UPDATE SET
            segment_index = EXCLUDED.segment_index,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            video_name = EXCLUDED.video_name,
            embedding = EXCLUDED.embedding,
            description = EXCLUDED.description,
            text_embedding = EXCLUDED.text_embedding,
            url = EXCLUDED.url;
        """
        await conn.executemany(insert_sql, records)
        print(f"✅ Successfully migrated {total_rows} records to AlloyDB!")

    except Exception as e:
        print(f"❌ Migration Error: {repr(e)}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
