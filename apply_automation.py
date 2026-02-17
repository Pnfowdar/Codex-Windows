
import os

path = r'd:\Projects\Codex-Windows\work\app\webview\assets\index-DEdUduNg.js'

# 1. helper logic to append
append_code = r"""
;(function(){try{window.updateCodexResetTime=function(d){try{var t=d.getTime()+60000;var s=localStorage.getItem('codex_reset_trigger');if(!s||Math.abs(s-t)>5000){localStorage.setItem('codex_reset_trigger',t);localStorage.setItem('codex_reset_status','pending');window.scheduleCodexReset&&window.scheduleCodexReset(t,'pending')}}catch(e){}};var tm=null;window.scheduleCodexReset=function(t,s){if(!t||s!=='pending')return;var d=Number(t)-Date.now();if(d<=0){run()}else{if(tm)clearTimeout(tm);tm=setTimeout(run,d);console.log('Codex Reset scheduled in '+Math.round(d/1000)+'s')}};async function run(){if(localStorage.getItem('codex_reset_status')!=='pending')return;localStorage.setItem('codex_reset_status','processing');try{var bs=Array.from(document.querySelectorAll('button'));var nb=bs.find(function(b){return b.textContent.includes('New Chat')||b.getAttribute('aria-label')==='New Chat'});if(!nb)throw new Error('No New Chat btn');nb.click();await new Promise(function(r){setTimeout(r,2000)});var ta=document.querySelector('textarea');if(!ta)throw new Error('No textarea');var pd=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value');pd.set.call(ta,'hi. stop.');ta.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(function(r){setTimeout(r,500)});var sb=document.querySelector('button[type="submit"]')||ta.parentNode.querySelector('button');if(sb)sb.click();localStorage.setItem('codex_reset_status','completed');console.log('Codex Reset Action Performed')}catch(e){console.error('Codex Reset Failed',e);localStorage.setItem('codex_reset_status','error')}};var it=localStorage.getItem('codex_reset_trigger');var is=localStorage.getItem('codex_reset_status');if(it)window.scheduleCodexReset(it,is)}catch(e){console.error('Codex Auto-Reset Init Error',e)}})();
"""

# 2. Logic to inject hook into uAe
# Target: function uAe(t,e=new Date){const n=$Mt(t);
# Replace with: function uAe(t,e=new Date){const n=$Mt(t);window.updateCodexResetTime&&window.updateCodexResetTime(n);

target_uAe = 'function uAe(t,e=new Date){const n=$Mt(t);'
replace_uAe = 'function uAe(t,e=new Date){const n=$Mt(t);window.updateCodexResetTime&&window.updateCodexResetTime(n);'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already appended
if 'window.updateCodexResetTime' in content and 'scheduleCodexReset' in content:
    print("Code likely already appended. Checking specific hook...")
else:
    print("Appending automation logic...")
    content += append_code

# Apply hook
if replace_uAe in content:
    print("Hook already present.")
elif target_uAe in content:
    print("Injecting hook into uAe...")
    content = content.replace(target_uAe, replace_uAe)
else:
    print("ERROR: uAe target signature not found!")
    # Debug snippet
    idx = content.find('function uAe')
    if idx != -1:
        print(f"Partial uAe match: {content[idx:idx+100]}")
    else:
        print("uAe not found at all")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Apply script finished.")
