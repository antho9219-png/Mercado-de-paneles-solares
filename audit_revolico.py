import json
from collections import Counter
from pathlib import Path

with open('paneles_solares_completo.json', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total records: {len(data)}")

# Precios válidos
precio_valid = [r for r in data if r.get('precio') not in [None, '', '000', 0]]
print(f"Con precio válido: {len(precio_valid)}")

# Moneda
moneda_ident = [r for r in data if r.get('moneda')]
print(f"Con moneda identificada: {len(moneda_ident)}")

# Potencia
potencia_ident = [r for r in data if r.get('potencia')]
print(f"Con potencia identificada: {len(potencia_ident)}")

# Marca y modelo
marca_modelo = [r for r in data if r.get('marca') and r.get('modelo')]
print(f"Con marca y modelo: {len(marca_modelo)}")
print(f"Solo marca: {len([r for r in data if r.get('marca') and not r.get('modelo')])}")

# Municipio
mun_ident = [r for r in data if r.get('municipio')]
print(f"Con municipio: {len(mun_ident)}")

# Nulos
for k in data[0].keys():
    nulls = sum(1 for r in data if r.get(k) is None or r.get(k) == '')
    print(f"Nulls {k}: {nulls}")
