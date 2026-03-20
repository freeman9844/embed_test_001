with open("app/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
replaced = False

while i < len(lines):
    line = lines[i]
    if '# Text ranking' in line:
         # 1. Outer index
         new_lines.append(line) # '# Text ranking'
         new_lines.append(lines[i+1]) # 'for rank, row...'
         new_lines.append(lines[i+2]) # 'item_id'
         
         # 2. Append ONLY the new multiplier line
         new_lines.append(lines[i+2][:14] + "rrf_scores[item_id] = rrf_scores.get(item_id, 0) + 1.25 * (1.0 / (rank + 60))\n")
         
         # 3. Advance past all garbage until we hit `lookup_item`
         i += 3
         while i < len(lines) and 'lookup_item' not in lines[i]:
              i += 1
              
         # 4. Append lookup item row
         new_lines.append(lines[i]) 
         replaced = True
         print("Replaced successfully")
         i += 1
         continue

    new_lines.append(line)
    i += 1

with open("app/main.py", "w") as f:
    f.write("".join(new_lines))

print(f"Finished. Replaced: {replaced}")
