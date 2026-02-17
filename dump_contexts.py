
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 3rd uAe occurrence
uAe_call = 'uAe('
start = 0
found_idx = -1
for i in range(3):
    idx = content.find(uAe_call, start)
    if idx == -1:
        break
    found_idx = idx
    start = idx + 1

if found_idx != -1:
    ctx = content[max(0, found_idx-1000):min(len(content), found_idx+1000)]
    with open(r'd:\Projects\Codex-Windows\context_uAe.txt', 'w', encoding='utf-8') as f:
        f.write(ctx)
    print("Wrote context_uAe.txt")
else:
    print("3rd uAe not found")

# 2. New Chat
nc_idx = content.find('>New Chat<') # JSX content?
if nc_idx == -1:
    nc_idx = content.find('"New Chat"')
if nc_idx != -1:
    ctx = content[max(0, nc_idx-1000):min(len(content), nc_idx+1000)]
    with open(r'd:\Projects\Codex-Windows\context_newchat.txt', 'w', encoding='utf-8') as f:
        f.write(ctx)
    print("Wrote context_newchat.txt")
else:
    print("New Chat not found")

# 3. localStorage - checking for wrapper or direct usage
ls_idx = content.find('localStorage')
if ls_idx != -1:
    ctx = content[max(0, ls_idx-1000):min(len(content), ls_idx+1000)]
    with open(r'd:\Projects\Codex-Windows\context_ls.txt', 'w', encoding='utf-8') as f:
        f.write(ctx)
    print("Wrote context_ls.txt")
else:
    print("localStorage not found")
