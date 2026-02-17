
path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

pos = 1591633
start = pos
end = min(len(content), pos + 1000)
with open(r'd:\Projects\Codex-Windows\uAe.txt', 'w', encoding='utf-8') as f_out:
    f_out.write(content[start:end])

# Also count usages
import re
usages = len(re.findall(r'[^a-zA-Z]uAe\(', content))
print(f"Usages of uAe(: {usages}")
