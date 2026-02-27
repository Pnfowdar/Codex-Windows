import re
with open(r'd:\Projects\Codex-Windows\work\app\webview\assets\index-BUvz-C55.js', 'r', encoding='utf-8') as f:
    text = f.read()

# search for Xs( usage
occurrences = [m.start() for m in re.finditer(r'Xs\(', text)]
with open('d:\\Projects\\Codex-Windows\\extracted_xs2.txt', 'w', encoding='utf-8') as out:
    for idx in occurrences:
        out.write(f"--- MATCH AT {idx} ---\n")
        out.write(text[max(0, idx - 150): min(len(text), idx + 150)])
        out.write("\n\n")
