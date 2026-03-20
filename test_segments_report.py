import lancedb
import os

DB_PATH = "app/database/lancedb"
db = lancedb.connect(DB_PATH)

try:
    table = db.open_table("video_scenes")
    results = table.search().limit(1000).to_list()

    
    print("--- 📹 Indexed Videos in Database ---")
    videos = list(set([row['video_name'] for row in results if row['id'] != 'init']))
    for vid in videos:
         count = len([r for r in results if r['video_name'] == vid])
         print(f"- {vid}: {count} segments indexed")

    print("\n--- 🔍 Detailed Segments Example ---")
    for r in results:
         if r['id'] == 'init': continue
         print(f"[{r['video_name']}] Seg {r['segment_index']}: {r['start_time']}s - {r['end_time']}s | Vec: {len(r['embedding'])}")

         
except Exception as e:
    print(f"Error reading LanceDB: {e}")
