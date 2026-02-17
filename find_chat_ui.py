
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Search for Textarea
print("--- Textarea Contexts ---")
ta_idx = content.find('textarea')
if ta_idx != -1:
    ctx = content[max(0, ta_idx-500):min(len(content), ta_idx+500)]
    print(ctx)
else:
    print("textarea not found")

# 2. Search for Placeholders
placeholders = ['Type a message', 'Ask anything', 'Send a message']
for p in placeholders:
    idx = content.find(p)
    if idx != -1:
        print(f"\n--- Placeholder '{p}' Context ---")
        ctx = content[max(0, idx-500):min(len(content), idx+500)]
        print(ctx)

# 3. Search for "New Chat" aria-label or accessible name
idx = content.find('aria-label="New Chat"')
if idx != -1:
    print("\n--- New Chat Aria Label Context ---")
    ctx = content[max(0, idx-500):min(len(content), idx+500)]
    print(ctx)
