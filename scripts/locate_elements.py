import os

path = os.path.join('mi_proyecto', 'catalogo', 'templates', 'catalogo', 'inicio.html')
targets = ['siteHeader', 'sub-header', 'site-header', 'mainHeader', 'header-actions']

with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f, 1):
        for t in targets:
            if t in line:
                print(f"Line {idx}: {line.strip()[:100]}")
                break
