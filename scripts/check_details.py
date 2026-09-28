import sqlite3

conn = sqlite3.connect('mi_proyecto/db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT id, texto, producto_id FROM catalogo_detalleproducto WHERE LOWER(texto) LIKE '%trapstar%' OR LOWER(texto) LIKE '%t star%' OR LOWER(texto) LIKE '%tirador%'")
rows = cur.fetchall()
print("Matches in catalogo_detalleproducto:", rows)
conn.close()
