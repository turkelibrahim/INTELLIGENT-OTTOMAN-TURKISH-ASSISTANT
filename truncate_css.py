import os

css_path = r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\frontend\src\app\globals.css"

with open(css_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "AUTH REFERENCE MATCH - LOGIN / REGISTER" in line:
        break
    new_lines.append(line)

# Remove the /* === that comes just before it
while new_lines and new_lines[-1].strip() in ["/* =====================================================", ""]:
    new_lines.pop()

with open(css_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
