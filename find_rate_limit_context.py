
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
target = 'rate limit resets'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find(target)
if idx != -1:
    start = max(0, idx - 500)
    end = min(len(content), idx + 500)
    print(f"--- Context around '{target}' ---")
    print(content[start:end])
else:
    print(f"'{target}' not found.")
