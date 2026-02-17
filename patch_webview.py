
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
target = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric"}).format(n)'
replacement = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric",hour:"numeric",minute:"numeric"}).format(n)'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if target in content:
    new_content = content.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched the file.")
else:
    print("Target string not found in file.")
    # Debug: print a snippet around where we expect it
    uAe_sig = 'function uAe('
    idx = content.find(uAe_sig)
    if idx != -1:
         print(f"Context found: {content[idx:idx+200]}")
