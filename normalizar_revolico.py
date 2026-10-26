import json
from pathlib import Path
from datetime import datetime

with open('paneles_solares_completo.json', encoding='utf-8') as f:
    data = json.load(f)

# Normalización básica
limpio = []
for r in data:
    item = dict(r)
    # Normalizar municipio
    mun = item.get('municipio')
    if mun:
        item['municipio_norm'] = mun.strip().title()
    else:
        item['municipio_norm'] = None
    # Normalizar provincia
    prov = item.get('provincia')
    if prov:
        item['provincia_norm'] = prov.strip()
    else:
        item['provincia_norm'] = None
    # Fuente
    item['fuente'] = 'Revolico'
    # Preservar precio/moneda separados, no convertir 000 a 0
    item['precio_limpio'] = item.get('precio')
    item['moneda_limpia'] = item.get('moneda')
    limpio.append(item)

Path('data').mkdir(exist_ok=True)
with open('data/revolico_limpio.json', 'w', encoding='utf-8') as f:
    json.dump(limpio, f, ensure_ascii=False, indent=2)

print('Guardado data/revolico_limpio.json con', len(limpio), 'registros')
