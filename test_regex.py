import re

with open(r'd:\Projects\Codex-Windows\work\app\webview\assets\index-BUvz-C55.js', 'r', encoding='utf-8') as f:
    text = f.read()

# The sunset gate ID is "2929582856"
# E.g. i="2929582856",e[0]=i):i=e[0];const s=Xs(i);
# We want to replace it to: const s=!1;
pattern = r'([a-zA-Z_$]+)="2929582856",[a-zA-Z_$]+\[\d+\]=\1\):\1=[a-zA-Z_$]+\[\d+\];const ([a-zA-Z_$]+)=Xs\(\1\);'
matches = re.findall(pattern, text)
print(f"Matches found: {matches}")

def replacer(m):
    original = m.group(0)
    var_name = m.group(2)
    # Reconstruct but replace Xs(..) with !1
    return original.replace(f"Xs({m.group(1)})", "!1")

new_text, count = re.subn(pattern, replacer, text)
print(f"Replaced {count} times.")
