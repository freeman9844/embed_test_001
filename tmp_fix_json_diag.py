with open("app/main.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
replaced = False

while i < len(lines):
    line = lines[i]
    if 'return {"query": q, "results": items}' in line:
         # Injection Of Diagnostics Dictionary
         prefix = line[:len(line) - len(line.lstrip())]
         
         new_lines.append(f"{prefix}diagnostics = {{\n")
         new_lines.append(f"{prefix}     'results_v': [\n")
         new_lines.append(f"{prefix}          {{'segment_index': int(r['segment_index']), 'description': r.get('description','No description')[:80]}} for r in results_v\n")
         new_lines.append(f"{prefix}     ],\n")
         new_lines.append(f"{prefix}     'results_t': [\n")
         new_lines.append(f"{prefix}          {{'segment_index': int(r['segment_index']), 'description': r.get('description','No description')[:80]}} for r in results_t\n")
         new_lines.append(f"{prefix}     ]\n")
         new_lines.append(f"{prefix}}}\n")
         new_lines.append(f"{prefix}return {{'query': q, 'results': items, 'diagnostics': diagnostics}}\n")
         
         replaced = True
         i += 1
         continue

    new_lines.append(line)
    i += 1

with open("app/main.py", "w") as f:
    f.write("".join(new_lines))

print(f"Finished. Replaced: {replaced}")
