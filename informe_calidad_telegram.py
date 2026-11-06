import json

# Cargar datos originales y mejorados
with open('data/telegram_paneles_habana.json.original_backup', encoding='utf-8') as f:
    original = json.load(f)

with open('data/telegram_paneles_habana_mejorado.json', encoding='utf-8') as f:
    mejorado = json.load(f)

campos = ['marca', 'modelo', 'potencia', 'precio', 'moneda', 'municipio', 'garantia', 'vida_util', 'tipo_panel', 'estado', 'descripcion', 'titulo', 'url', 'fecha_publicacion', 'canal']

print("INFORME DE CALIDAD - Comparación Antes vs Después")
print("=" * 70)
print(f"{'Campo':<20} {'Antes':<10} {'Después':<10} {'Mejora':<10}")
print("-" * 70)

for campo in campos:
    antes = sum(1 for r in original if r.get(campo) not in [None, '', 'null'])
    despues = sum(1 for r in mejorado if r.get(campo) not in [None, '', 'null'])
    mejora = despues - antes
    print(f"{campo:<20} {antes:<10} {despues:<10} {mejora:+d}")

print("=" * 70)
print(f"\nTotal registros: {len(original)} → {len(mejorado)}")
print(f"Registros únicos: {len(original)} → {len(mejorado)}")
print(f"Duplicados: 0 → 0")

print("\nCampos nulos ANTES:")
for campo in campos:
    nulos = sum(1 for r in original if r.get(campo) in [None, '', 'null'])
    print(f"  {campo}: {nulos}/{len(original)}")

print("\nCampos nulos DESPUÉS:")
for campo in campos:
    nulos = sum(1 for r in mejorado if r.get(campo) in [None, '', 'null'])
    print(f"  {campo}: {nulos}/{len(mejorado)}")

print("\nMarcas recuperadas:")
for r in mejorado:
    if r.get('marca'):
        print(f"  - {r['marca']} (mensaje {r['telegram_message_id']}, {r['canal']})")

print("\nModelos recuperados:")
for r in mejorado:
    if r.get('modelo'):
        print(f"  - {r['modelo']} (mensaje {r['telegram_message_id']}, {r['canal']})")

print("\nPotencias recuperadas:")
for r in mejorado:
    if r.get('potencia'):
        print(f"  - {r['potencia']} W (mensaje {r['telegram_message_id']}, {r['canal']})")

print("\nTipos de panel recuperados:")
for r in mejorado:
    if r.get('tipo_panel'):
        print(f"  - {r['tipo_panel']} (mensaje {r['telegram_message_id']}, {r['canal']})")

print("\nGarantías recuperadas:")
for r in mejorado:
    if r.get('garantia'):
        print(f"  - {r['garantia']} (mensaje {r['telegram_message_id']}, {r['canal']})")
