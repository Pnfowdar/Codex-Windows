
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
uAe_call = 'uAe('

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

count = content.count(uAe_call)
print(f"'uAe(' found {count} times.")

# Find contexts
start = 0
for i in range(count):
    idx = content.find(uAe_call, start)
    if idx == -1:
        break
    
    # context around the call
    ctx_start = max(0, idx - 100)
    ctx_end = min(len(content), idx + 200)
    print(f"--- Occurrence {i+1} ---")
    print(content[ctx_start:ctx_end])
    print("---------------------")
    start = idx + 1
