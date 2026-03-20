with open("app/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
replaced_v = False
replaced_t = False

while i < len(lines):
    line = lines[i]
    
    # 1. Video Ranking Boost
    if '# Video ranking' in line and i+4 < len(lines) and 'item_id = row' in lines[i+2]:
         new_lines.append(line) # '# Video ranking'
         new_lines.append(lines[i+1]) # 'for rank, row in enumerate(results_v):'
         new_lines.append(lines[i+2]) # 'item_id = row['id']'
         
         prefix = lines[i+2][:len(lines[i+2]) - len(lines[i+2].lstrip())]
         
         new_lines.append(f"{prefix}score = 1.0 / (rank + 60)\n")
         new_lines.append(f"{prefix}if q_norm.lower() in row.get('description', '').lower():\n")
         new_lines.append(f"{prefix}     score += 0.5 # Substring Match Bonus\n")
         new_lines.append(f"{prefix}rrf_scores[item_id] = rrf_scores.get(item_id, 0) + score\n")
         
         i += 4 # Skip old math (line 421 in original)
         replaced_v = True
         continue

    # 2. Text Ranking Boost
    if '# Text ranking' in line and i+4 < len(lines) and 'item_id = row' in lines[i+2]:
         new_lines.append(line) # '# Text ranking'
         new_lines.append(lines[i+1]) # 'for rank, row in enumerate(results_t):'
         new_lines.append(lines[i+2]) # 'item_id = row['id']'
         
         prefix = lines[i+2][:len(lines[i+2]) - len(lines[i+2].lstrip())]
         
         new_lines.append(f"{prefix}score = 1.25 * (1.0 / (rank + 60))\n")
         new_lines.append(f"{prefix}if q_norm.lower() in row.get('description', '').lower():\n")
         new_lines.append(f"{prefix}     score += 0.5 # Substring Match Bonus\n")
         new_lines.append(f"{prefix}rrf_scores[item_id] = rrf_scores.get(item_id, 0) + score\n")
         
         i += 4 # Skip old math
         replaced_t = True
         continue

    new_lines.append(line)
    i += 1

with open("app/main.py", "w") as f:
    f.write("".join(new_lines))

print(f"Finished. Video Replaced: {replaced_v}, Text Replaced: {replaced_t}")
