"""
Script para abrir un tunel ngrok al servidor Django en el puerto 8000.
Ejecutar desde la carpeta mi_proyecto con el venv activo.
"""
from pyngrok import ngrok

# Abrir tunnel
tunnel = ngrok.connect(8000)
public_url = tunnel.public_url

print("=" * 60)
print("  TRAPSTAR x CENTRAL CEE — Acceso desde Telefono")
print("=" * 60)
print(f"\n  URL publica: {public_url}")
print(f"\n  Abre este link en tu telefono o cualquier dispositivo!")
print("\n  Presiona Ctrl+C para detener el tunel.")
print("=" * 60)

try:
    ngrok.get_ngrok_process().proc.wait()
except KeyboardInterrupt:
    print("\nTunel cerrado.")
    ngrok.kill()
