
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
target = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric"}).format(n)'
replacement = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric",hour:"numeric",minute:"numeric"}).format(n)'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

patched = False
with open(path, 'w', encoding='utf-8') as f:
    for i, line in enumerate(lines):
        if target in line:
            print(f"Found target on line {i+1}")
            line = line.replace(target, replacement)
            patched = True
        f.write(line)

if patched:
    print("Successfully patched the file.")
else:
    print("Target string not found in file.")
