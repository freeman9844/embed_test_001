import subprocess
import os
import glob

def get_duration(file_path):
    cmd = [
        "bin/ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        return f"Err: {e}"

def test_split(video_path, out_pattern, mode="copy"):
    ffmpeg_bin = "bin/ffmpeg"
    if mode == "copy":
        command = [
            ffmpeg_bin, "-y", "-i", video_path,
            "-f", "segment", "-segment_time", "10",
            "-c", "copy", out_pattern
        ]
    else: # Re-encode
        command = [
            ffmpeg_bin, "-y", "-i", video_path,
            "-f", "segment", "-segment_time", "10",
            "-reset_timestamps", "1",
            out_pattern
        ]
    
    print(f"\n--- 🎬 Testing Split Mode: {mode} ---")
    try:
         subprocess.run(command, capture_output=True, text=True, check=True)
         segments = sorted(glob.glob(out_pattern.replace("%03d", "*")))
         for i, seg in enumerate(segments):
              duration = get_duration(seg)
              print(f"Segment {i+1}: {os.path.basename(seg)} -> Duration: {duration}s")
    except Exception as e:
         print(f"Error: {e}")

# Find any uploaded videos
uploads_dir = "app/database/uploads"
if os.path.exists(uploads_dir):
     v_files = [f for f in os.listdir(uploads_dir) if f.endswith(".mp4")]
     if v_files:
          source = os.path.join(uploads_dir, v_files[0])
          print(f"Testing on {source}")
          os.makedirs("tmp_test/copy", exist_ok=True)
          os.makedirs("tmp_test/reencode", exist_ok=True)
          
          test_split(source, "tmp_test/copy/seg_%03d.mp4", mode="copy")
          test_split(source, "tmp_test/reencode/seg_%03d.mp4", mode="reencode")
     else:
          print("No upload video found to test split verification.")
else:
     print("Uploads dir doesn't exist.")
