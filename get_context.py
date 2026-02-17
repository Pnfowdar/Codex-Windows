
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

pos = 1591633
# Search for uAe around this position
start = max(0, pos - 500)
end = min(len(content), pos + 1000)
# Look for function uAe in this window to confirm
window = content[start:end]
idx = window.find('function uAe')
if idx != -1:
    print(f"Found function uAe at relative {idx}")
    print(window[idx:idx+500])
else:
    print("function uAe not found in window.")
    print(window)
