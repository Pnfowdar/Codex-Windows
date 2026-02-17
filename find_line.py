
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
target = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric"}).format(n)'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = False
for i, line in enumerate(lines):
    if target in line:
        print(f"Found on line {i+1}")
        found = True
        break

if not found:
    print("Target not found.")
