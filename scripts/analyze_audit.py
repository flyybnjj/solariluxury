import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('capturas_mobile_audit/fase0_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== 1. AUDITORIA DE VIEWPORT META ===")
for tmpl, info in data['viewport_meta'].items():
    if not info['has_viewport_fit_cover'] or not info['has_viewport_meta']:
        print(f"Template: {tmpl}")
        print(f"  has_viewport_meta: {info['has_viewport_meta']}")
        print(f"  has_viewport_fit_cover: {info['has_viewport_fit_cover']}")

print("\n=== 2. OVERFLOWS DETECTADOS ===")
overflow_count = 0
for slug, vps in data['pages'].items():
    for vp, res in vps.items():
        if res.get('hasOverflow'):
            overflow_count += 1
            print(f"Pagina: {slug:<14} | Viewport: {vp:<16} | Win: {res['winW']}px | Doc: {res['scrollW']}px | Desbordados: {res['overflowingCount']}")
            if res.get('samples'):
                for s in res['samples'][:3]:
                    print(f"   -> <{s['tag']} class=\"{s['className']}\" id=\"{s['id']}\" width={s['width']} left={s['left']}>")

if overflow_count == 0:
    print("No se detectaron overflows en las paginas auditadas.")
else:
    print(f"Total de combinaciones pagina/viewport con overflow: {overflow_count}")
