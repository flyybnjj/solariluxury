import os

src_dir = r"C:\Users\avalo\Desktop\cap\codigo_plantillas"
templates_dir = r"C:\Users\avalo\Documents\tienda\mi_proyecto\usuarios\templates\emails"
os.makedirs(templates_dir, exist_ok=True)
usuarios_templates_dir = r"C:\Users\avalo\Documents\tienda\mi_proyecto\usuarios\templates\usuarios"

mapping = {
    "01_preparando_pedido.html": os.path.join(templates_dir, "email_preparando_pedido.html"),
    "02_pedido_despachado.html": os.path.join(templates_dir, "email_pedido_despachado.html"),
    "03_pedido_entregado.html": os.path.join(templates_dir, "email_pedido_entregado.html"),
    "04_recibo_oficial_compra.html": os.path.join(templates_dir, "email_recibo_oficial_compra.html"),
    "05_codigo_seguridad_apple_id.html": os.path.join(usuarios_templates_dir, "email_pin_acceso.html"),
    "06_invitacion_drop_vip.html": os.path.join(templates_dir, "email_invitacion_drop_vip.html"),
}

for src_name, target_path in mapping.items():
    p_src = os.path.join(src_dir, src_name)
    with open(p_src, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace Solari / SOLARI / solari -> Solary / SOLARY / solary
    content = content.replace("SOLARI", "SOLARY")
    content = content.replace("Solari", "Solary")
    content = content.replace("solari", "solary")

    # 2. Replace Alejandro Valenzuela -> Test Test with dynamic variables
    content = content.replace('"Alejandro Valenzuela"', '"Test Test"')
    content = content.replace("'Alejandro Valenzuela'", "'Test Test'")
    content = content.replace("Alejandro Valenzuela", '{{ cliente_nombre|default:orden.nombre_cliente|default:"Test Test" }}')
    content = content.replace('{{ orden.nombre_cliente|default:"Test Test" }}', '{{ cliente_nombre|default:orden.nombre_cliente|default:"Test Test" }}')

    # 3. For 05 PIN OTP template
    if "05_codigo_seguridad" in src_name:
        content = content.replace(
            '{{ pin|default:"482 910" }}',
            '{% if pin_spaced %}{{ pin_spaced }}{% elif pin %}{{ pin|slice:":3" }} &nbsp; {{ pin|slice:"3:" }}{% else %}482 910{% endif %}'
        )

    # 4. Use crisp real product images
    content = content.replace(
        "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=700&q=80",
        "https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/af1_syna_email.png"
    )
    content = content.replace(
        "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=700&q=80",
        "https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/tech_fleece_email.png"
    )
    content = content.replace(
        "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?auto=format&fit=crop&w=700&q=80",
        "https://raw.githubusercontent.com/flyyyy98/solariluxury/main/mi_proyecto/static/img/emails/beanie_email.png"
    )

    # Write to Django templates
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Also update Desktop source file so user has it updated there
    with open(p_src, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] {src_name} -> {target_path}")

print("=== ACTUALIZACIÓN DE PLANTILLAS COMPLETADA ===")
