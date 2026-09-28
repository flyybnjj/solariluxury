import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('capturas_mobile_audit/animations_audit.json', 'r', encoding='utf-8') as f:
    anims = json.load(f)

print(f"Total Keyframes: {len(anims['keyframes'])}")
for k, v in list(anims['keyframes'].items())[:25]:
    print(f"  @keyframes {k:<25} ({v})")

print(f"\nTotal JS listeners: {len(anims['js_mouse_listeners'])}")
for l in anims['js_mouse_listeners'][:20]:
    print(f"  {l['event']:<12} in {l['file']}")
