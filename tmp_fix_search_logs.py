with open("app/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
replaced = False

while i < len(lines):
    line = lines[i]
    if '# 3. Reciprocal Rank Fusion (RRF)' in line:
         # 1. Detect EXACT leading whitespace of the current block
         prefix = line[:len(line) - len(line.lstrip())]
         print(f"Detected prefix bytes: {repr(prefix)}")
         
         # Safe Injection with matching prefix
         new_lines.append(line) # Keep line 398
         new_lines.append(f"{prefix}print(f\"\\n--- 🔍 RRF Search Debug: Query='{{q}}' ---\")\n")
         new_lines.append(f"{prefix}print(f\"🎥 Video Search Results ({{len(results_v)}} items):\")\n")
         new_lines.append(f"{prefix}for r, row in enumerate(results_v):\n")
         new_lines.append(f"{prefix}     print(f\"  Rank {{r+1}}: Seg={{row['segment_index']}} | {{row.get('description','')[:40]}}...\")\n")
         new_lines.append(f"{prefix}print(f\"📝 Text Search Results ({{len(results_t)}} items):\")\n")
         new_lines.append(f"{prefix}for r, row in enumerate(results_t):\n")
         new_lines.append(f"{prefix}     print(f\"  Rank {{r+1}}: Seg={{row['segment_index']}} | {{row.get('description','')[:40]}}...\")\n\n")
         
         # Skip existing failed error injections (print statements and setup)
         replaced = True
         
         i += 1
         # Advance until we meet `rrf_scores = {}`
         while i < len(lines) and 'rrf_scores = {}' not in lines[i]:
              i += 1
         
         new_lines.append(f"{prefix}rrf_scores = {{}}\n")
         new_lines.append(f"{prefix}lookup_item = {{}}\n")
         
         i += 1
         if i < len(lines) and 'lookup_item = {}' in lines[i]:
              i += 1
         continue

    new_lines.append(line)
    i += 1

with open("app/main.py", "w") as f:
    f.write("".join(new_lines))

print(f"Finished. Replaced: {replaced}")
