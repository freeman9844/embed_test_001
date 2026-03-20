with open("app/templates/index.html", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
replaced = False

while i < len(lines):
    line = lines[i]
    if '<div class="card-cover">' in line and i+4 < len(lines) and '<i class="fa-regular fa-file-video">' in lines[i+1]:
         # Safe Injection
         new_lines.append('                             <div class="card-cover" style="height: auto; padding: 0.5rem;">\n')
         new_lines.append('                                 <video src="${item.url}" controls style="width: 100%; border-radius: 12px; max-height: 180px;"></video>\n')
         new_lines.append('                                 <div class="score-indicator" style="top: 1rem; right: 1rem;">RRF: ${item.score.toFixed(4)}</div>\n')
         new_lines.append('                             </div>\n')
         i += 4 # Skip <div class="card-cover"> through </div> (4 lines)
         replaced = True
         print("Replaced successfully")
         continue
    
    new_lines.append(line)
    i += 1

with open("app/templates/index.html", "w") as f:
    f.write("".join(new_lines))

print(f"Finished. Replaced: {replaced}")
