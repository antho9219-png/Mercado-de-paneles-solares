# Mercado solar en La Habana — prototipo de análisis y storytelling

Prototipo reproducible que responde una pregunta concreta con datos reales:

> **¿Qué tan transparente y comparable es el mercado solar que aparece en La Habana?**

Se apoya en 382 anuncios (Telegram + Revolico), 35 compras declaradas y la serie
oficial de electricidad de la ONEI (2019-2022).

---

## Estructura

```
proyecto/
├── data/
│   ├── raw/              # JSON originales, sin tocar
│   │   ├── telegram_anuncios.json      (352 anuncios, con fecha)
│   │   ├── revolico_anuncios.json      (30 anuncios, sin fecha)
│   │   └── entrevistas.json            (35 compras, sin fecha)
│   └── fuentes/          # descargas de sitios oficiales
│       ├── onei_10.14_balance_electricidad.xlsx
│       ├── onei_mineria_y_energia.html
│       └── opendata_banco_mundial.csv
├── notebooks/
│   └── storytelling.ipynb   # narrativa + 11 gráficos renderizados
├── scripts/
│   ├── 01_carga_limpieza.py
│   ├── 02_analisis.py
│   └── 03_graficos.py
├── outputs/
│   ├── figuras/          # 12 PNG
│   └── tablas/           # 18 CSV de resultados
├── FUENTES.md            # URLs, fechas, hashes y campos usados
└── README.md
```

---

## Requisitos

Python 3.10 o superior.

```bash
pip install -r requirements.txt
```

Dependencias: `pandas`, `numpy`, `matplotlib`, `openpyxl`, `nbformat`, `nbclient`.

---

## Cómo reproducirlo

Desde la raíz de `proyecto/`, en este orden:

```bash
python scripts/01_carga_limpieza.py   # lee data/ y escribe outputs/tablas/*_limpio.csv
python scripts/02_analisis.py         # escribe las 15 tablas de análisis
python scripts/03_graficos.py         # escribe los 11 PNG en outputs/figuras/
```

Opcionalmente, para abrir la historia:

```bash
jupyter notebook notebooks/storytelling.ipynb
```

El cuaderno **ejecuta el pipeline por sí mismo** en la celda de la sección 4, así que
también funciona con *Run All* sin haber corrido los scripts antes.

---

## Reglas de datos (no negociables en este proyecto)

1. **No se inventa ni se imputa nada.** Lo ausente queda `NaN` y se reporta.
2. **No se convierten monedas** sin una serie oficial de tipos de cambio: los 9
   anuncios en EUR/CUP quedan fuera de los análisis de precio.
3. **Los errores se marcan, no se borran**: `flag_sin_precio`, `flag_precio_bajo`,
   `flag_potencia_imposible`, `flag_moneda_no_usd`.
4. **No se usan los archivos sintéticos** (`ejemplo_anuncios.json`,
   `output/paneles_solares.json`): 25 de sus 26 filas son de ejemplo.
5. **Toda fuente web queda descargada** en `data/fuentes/` y documentada en `FUENTES.md`
   con URL, fecha y SHA-256.

---

## Resultados principales

| Hallazgo | Cifra |
|---|---|
| Electricidad disponible en Cuba, 2019 → 2022 (ONEI) | **−13,4 %** (21 155 → 18 323 GWh) |
| Importación de generación móvil, 2019 → 2022 (ONEI) | **+476 %** (449 → 2 591 GWh) |
| Anuncios publicados | 352 en 2 canales, 2022-06 → 2026-10 |
| Anuncios de panel solar sin precio | **58,0 %** (112 de 193) |
| Anuncios de kit solar sin precio | **9,5 %** (4 de 42) |
| Precio mediano anunciado (panel, USD/W) | **0,364** (n=71) |
| Precio mediano pagado (panel, USD/W) | **0,267** (n=35) |
| Brecha oferta vs compra | **−27 %** |
| Anuncios que mencionan garantía | **11,9 %** (42 de 352) |
| Compras con garantía obtenida | **51,4 %** (18 de 35); 12 de ellas de **1 mes** |
| Marca líder en la oferta | **MUST**, 62 de 98 anuncios con marca (63 %) |
| Presencia de MUST en las compras | **0 de 35** |
| Compras que incluyen batería | **31 de 35** (89 %) |
| Compras que incluyen inversor | **15 de 35** (43 %) |

---

## Limitaciones

- **n=35** en la demanda: comparaciones descriptivas, no inferenciales.
- **Sin fecha de compra** en `entrevistas.json` y **sin fecha** en Revolico: no hay
  serie temporal de la demanda.
- **94,9 %** de los anuncios de Telegram no tiene municipio: no se hizo análisis territorial.
- Los precios son **declaraciones**, no facturas verificadas.
- La serie de ONEI termina en 2022: es contexto, no causa.

---

## Fuentes

Todas las fuentes, con URL exacta, fecha de descarga, archivo guardado, campos usados
y hash SHA-256, están en **`FUENTES.md`**.
