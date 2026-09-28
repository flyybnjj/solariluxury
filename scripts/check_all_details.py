import sqlite3

conn = sqlite3.connect('mi_proyecto/db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT id, texto, producto_id FROM catalogo_detalleproducto")
rows = cur.fetchall()
for r in rows:
    if any(k in r[1].lower() for k in ['trap', 'star', 'london']):
        print("Detail match:", r)

conn.close()
