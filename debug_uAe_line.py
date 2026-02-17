
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

if len(lines) >= 1620:
    line = lines[1619] # 0-indexed
    print(f"Line 1620 length: {len(line)}")
    print(f"Line 1620 repr: {repr(line)}")
    
    target = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric"}).format(n)'
    if target in line:
        print("Target found in line.")
    else:
        print("Target NOT found in line.")
else:
    print(f"File has only {len(lines)} lines.")
