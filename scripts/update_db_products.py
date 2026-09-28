import sqlite3

conn = sqlite3.connect('mi_proyecto/db.sqlite3')
cur = conn.cursor()

# 1. Update detail 70
cur.execute("""
    UPDATE catalogo_detalleproducto 
    SET texto = "CIERRE CROMADO BIDIRECCIONAL CON TIRADOR 'SL' SOLARILUXURY" 
    WHERE id = 70
""")

# 2. Update product images to authentic solariluxury images
updates = [
    (17, 'img/solariluxury_puffer_hero.jpg'),
    (18, 'img/solariluxury_tracksuit.jpg'),
    (19, 'img/solariluxury_hoodie_blue.jpg'),
    (20, 'img/solariluxury_zip_hoodie.jpg'),
    (21, 'img/solariluxury_tshirt.jpg'),
    (22, 'img/solariluxury_bag.jpg'),
    (32, 'img/solariluxury_camo_hoodie.jpg'),
]

for pid, img in updates:
    cur.execute("UPDATE catalogo_producto SET imagen = ? WHERE id = ?", (img, pid))
    print(f"Updated product {pid} image to {img}")

conn.commit()
print("Database updated successfully!")
conn.close()
