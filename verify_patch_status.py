
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
target_new = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric",hour:"numeric",minute:"numeric"}).format(n)'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if target_new in content:
    print("VERIFICATION SUCCESS: New format string found in file.")
else:
    print("VERIFICATION FAILURE: New format string NOT found.")
    # Check for partial match or old string
    old = 'new Intl.DateTimeFormat(void 0,{month:"short",day:"numeric"}).format(n)'
    if old in content:
        print("OLD format string still present.")
