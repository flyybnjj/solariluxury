import os, glob

template_files = glob.glob('mi_proyecto/**/templates/**/*.html', recursive=True)

for path in template_files:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content
    content = content.replace('TRAPSTAR LONDON × CENTRAL CEE', 'SOLARILUXURY × CENTRAL CEE')
    content = content.replace('TRAPSTAR LONDON x CENTRAL CEE', 'SOLARILUXURY × CENTRAL CEE')
    content = content.replace('Trapstar London × Central Cee', 'Solariluxury × Central Cee')
    content = content.replace('Trapstar London x Central Cee', 'Solariluxury × Central Cee')
    content = content.replace('TRAPSTAR LONDON', 'SOLARILUXURY')
    content = content.replace('Trapstar London', 'Solariluxury')
    content = content.replace('TRAPSTAR × CENTRAL CEE', 'SOLARILUXURY × CENTRAL CEE')
    content = content.replace('Trapstar x Central Cee', 'Solariluxury × Central Cee')
    content = content.replace('Trapstar', 'Solariluxury')
    content = content.replace('TRAPSTAR', 'SOLARILUXURY')

    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated branding in:', path)

print('All templates checked and updated!')
