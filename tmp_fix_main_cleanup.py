import os

filepath = "/Users/jungwoonlee/embed_test_001/app/main.py"
with open(filepath, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "shutil.rmtree(tmp_dir)" in line:
         # Skip this line
         continue
    new_lines.append(line)

with open(filepath, "w") as f:
    f.write("".join(new_lines))

print("Dangling cleanup removed.")
