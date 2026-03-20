with open("app/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
replaced = False

while i < len(lines):
    line = lines[i]
    if '# 1. Embed textual query' in line:
         # 1. Outer index
         prefix = line[:len(line) - len(line.lstrip())]
         
         # Safe Injection with typo normalization
         new_lines.append(f"{prefix}# 1. Typo Normalization and Query Expansion\n")
         new_lines.append(f"{prefix}q_norm = q.replace('깍', '깎')\n\n")
         new_lines.append(f"{prefix}# 2. Embed textual query\n")
         
         # Skip the original `# 1. Embed` comment
         i += 1
         continue

    if 'embed_content_rest(content_payload={"parts": [{"text": q}]})' in line:
         # Replace `q` with `q_norm`
         new_lines.append(line.replace('q', 'q_norm'))
         replaced = True
         i += 1
         continue

    if 'embed_text_005_rest(q)' in line:
         # Replace `q` with `q_norm`
         new_lines.append(line.replace('q', 'q_norm'))
         i += 1
         continue

    new_lines.append(line)
    i += 1

with open("app/main.py", "w") as f:
    f.write("".join(new_lines))

print(f"Finished. Replaced: {replaced}")
