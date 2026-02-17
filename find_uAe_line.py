
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
target = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric"}).format(n)'
uAe_sig = 'function uAe('

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if uAe_sig in line:
        print(f"'function uAe(' found on line {i+1}")
        if target in line:
            print(f"Target string ALSO found on line {i+1}")
        else:
            print(f"Target string NOT found on line {i+1}")
        # Print snippet
        start = line.find(uAe_sig)
        print(f"Snippet: {line[start:start+100]}...")
