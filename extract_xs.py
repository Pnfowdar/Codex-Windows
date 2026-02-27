import sys, re
with open(r'd:\Projects\Codex-Windows\work\app\webview\assets\index-BUvz-C55.js', 'r', encoding='utf-8') as f:
    text = f.read()

occurrences = [m.start() for m in re.finditer(r'function Xs\b|const Xs\s*=', text)]
with open('d:\\Projects\\Codex-Windows\\extracted_xs.txt', 'w', encoding='utf-8') as out:
    for idx in occurrences:
        out.write(f"--- MATCH AT {idx} ---\n")
        out.write(text[max(0, idx - 100): min(len(text), idx + 500)])
        out.write("\n\n")
