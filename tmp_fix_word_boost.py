with open("app/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
replaced_count = 0

while i < len(lines):
    line = lines[i]
    if "if q_norm.lower() in row.get('description', '').lower():" in line:
         prefix = line[:len(line) - len(line.lstrip())]
         
         new_lines.append(f"{prefix}target_words = [w for w in q_norm.split() if w not in ['장면', '모습', '영상', '사진']]\n")
         new_lines.append(f"{prefix}if any(w.lower() in row.get('description', '').lower() for w in target_words):\n")
         
         i += 1 # Skip the old if statement outer block header
         print(f"Replaced condition on line index {i}")
         replaced_count += 1
         continue

    new_lines.append(line)
    i += 1

with open("app/main.py", "w") as f:
    f.write("".join(new_lines))

print(f"Finished. Total Replaced: {replaced_count}")
