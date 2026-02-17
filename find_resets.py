
import re

path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

queries = [r'function uAe', r'uAe=']

for q in queries:
    print(f"Searching for '{q}'...")
    matches = [m.start() for m in re.finditer(re.escape(q), content)]
    for m in matches:
        print(f"Match for '{q}' at {m}:")
        start = max(0, m - 100)
        end = min(len(content), m + 500)
        print(content[start:end])
        print("-" * 50)
