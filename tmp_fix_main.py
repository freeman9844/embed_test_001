import os

filepath = "/Users/jungwoonlee/embed_test_001/app/main.py"
with open(filepath, "r") as f:
    content = f.read()

# 1. Update the loop insertion to collect segments_metadata
target_old = """if embedding_vector:
                     data_to_insert.append({
                         "id": str(uuid.uuid4()),
                         "segment_index": index,
                         "start_time": float(start_time),
                         "end_time": float(end_time),
                         "video_name": video_name,
                         "embedding": embedding_vector
                     })"""

target_new = """if embedding_vector:
                     data_to_insert.append({
                         "id": str(uuid.uuid4()),
                         "segment_index": index,
                         "start_time": float(start_time),
                         "end_time": float(end_time),
                         "video_name": video_name,
                         "embedding": embedding_vector
                     })
                     segments_metadata.append({
                         "index": index,
                         "start_time": float(start_time),
                         "end_time": float(end_time),
                         "url": f"/static/segments/{video_id}/segment_{index:03d}.mp4",
                         "dimensions": len(embedding_vector)
                     })"""

if target_old in content:
     content = content.replace(target_old, target_new)
     print("Loop append updated.")
else:
     print("Loop append TARGET NOT FOUND.")

# 2. Update completion and remove cleanup
cleanup_old = """        # Step 3: Insert to Vector DB
        if data_to_insert:
            process_status[video_id]["logs"].append("Saving to Vector DB...")
            table.add(data_to_insert)
            process_status[video_id]["status"] = "Completed"
            process_status[video_id]["progress"] = 100
        else:
             process_status[video_id]["status"] = "Failed"
             process_status[video_id]["logs"].append("No embeddings generated, failed.")

    except Exception as e:
         process_status[video_id]["status"] = "Failed"
         process_status[video_id]["logs"].append(f"General processing error: {e}")
         print(f"Background process error: {e}")
    finally:
         # Clean up tmp directory
         if os.path.exists(tmp_dir):
              shutil.rmtree(tmp_dir)"""

cleanup_new = """        # Step 3: Insert to Vector DB
        if data_to_insert:
            process_status[video_id]["logs"].append("Saving to Vector DB...")
            table.add(data_to_insert)
            process_status[video_id]["status"] = "Completed"
            process_status[video_id]["progress"] = 100
            process_status[video_id]["segments_metadata"] = segments_metadata
        else:
             process_status[video_id]["status"] = "Failed"
             process_status[video_id]["logs"].append("No embeddings generated, failed.")

    except Exception as e:
         process_status[video_id]["status"] = "Failed"
         process_status[video_id]["logs"].append(f"General processing error: {e}")
         print(f"Background process error: {e}")
    finally:
         pass"""

if cleanup_old in content:
     content = content.replace(cleanup_old, cleanup_new)
     print("Cleanup block updated.")
else:
     # Test with softer matches or regex
     print("Cleanup block TARGET NOT FOUND.")

with open(filepath, "w") as f:
    f.write(content)
