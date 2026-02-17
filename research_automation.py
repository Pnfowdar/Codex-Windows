
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
uAe_call = 'uAe('

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Expand uAe context
print("--- uAe Contexts ---")
start = 0
for i in range(3):
    idx = content.find(uAe_call, start)
    if idx == -1:
        break
    
    ctx_start = max(0, idx - 200) # expanded
    ctx_end = min(len(content), idx + 200)
    print(f"Occurrence {i+1}:")
    print(content[ctx_start:ctx_end])
    print("-" * 20)
    start = idx + 1

# 2. Search for "New Chat"
print("\n--- 'New Chat' Contexts ---")
nc_idx = content.find('"New Chat"') # Check for common string
if nc_idx == -1:
    nc_idx = content.find("'New Chat'")
if nc_idx != -1:
    print(content[nc_idx-100:nc_idx+100])
else:
    print("'New Chat' not found.")

# 3. Search for localStorage
print("\n--- localStorage Usage ---")
ls_idx = content.find("localStorage.setItem")
if ls_idx != -1:
    print(content[ls_idx-100:ls_idx+100])
else:
    print("localStorage.setItem not found.")
