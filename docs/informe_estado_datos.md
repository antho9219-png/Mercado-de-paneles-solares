# Informe de estado y calidad de los datos

**Fecha del informe:** 2026-10-16
**Ámbito:** mercado de paneles solares y equipos de energía solar en La Habana, Cuba.
**Archivos revisados:** `data/raw/paneles_solares_habana.csv` y
`data/processed/paneles_solares_habana_limpio.csv` (26 registros).

> Este informe NO añade datos: solo describe lo que ya existe en el conjunto.

---

## 1. Resumen ejecutivo

| Concepto | Valor |
|---|---|
| Registros totales | **26** |
| Anuncios **reales** | **1** (`fuente = revolico`) |
| Registros de **ejemplo** (sintéticos) | **25** (`fuente = ejemplo`, URLs `https://example.org/...`) |
| Duplicados | **0** |
| Registros incompletos (obligatorios: `ad_id`, `title`, `url`) | **0** |

**Conclusión clave:** el conjunto **no son 26 anuncios reales**. Solo **1** es un
anuncio real; los **25** restantes son datos de **ejemplo** creados para probar el
flujo del programa. Cualquier estadística de mercado debe calcularse **solo con
el registro real** (`source = revolico`).

---

## 2. ¿Son anuncios reales de paneles solares? (verificación)

* **Real (1):** `57503108` — "PANEL SOLAR 660W AIKO BIFACIAL CONTENEDOR 720
  PANELES", Revolico, municipio Plaza de la Revolución. Es un **contenedor de
  720 paneles** (producto a granel, no un panel suelto).
* **Ejemplo (25):** marcados con `fuente = ejemplo` y URLs `example.org`; **no
  son anuncios reales**.
* **No todo es "panel":** por tipo de producto hay 17 `panel solar`, 4
  `kit solar`, 3 `inversor solar` y 2 `bateria solar`. El proyecto cubre
  "equipos de energía solar", no solo paneles.

---

## 3. Verificación de campos del anuncio real (`57503108`)

| Campo pedido | Valor verificado | Estado |
|---|---|---|
| Precio / moneda | 145 USD | Presente (ver §6: ambigüedad) |
| Potencia | 660 W (Pmax) | Presente |
| Marca | AIKO (fabricante: AIKO Solar) | Presente |
| Modelo | AIKO-A660-MDE72Dw (Serie Stellar 3N+72) | Presente |
| Vida útil | — | **Ausente** (no figura en el anuncio) |
| Garantía | Rendimiento lineal: 30 años; producto: "consultar condiciones del proveedor" | Presente (parcial) |
| Municipio | Plaza de la Revolución (La Habana) | Presente |
| Fecha de publicación | — | **Ausente** (solo `updatedOnByUser` = 2026-10-10T13:43:12Z) |

Datos de contacto (nombre y teléfono del vendedor) **no se registraron**, por ser
datos personales.

---

## 4. Completitud de campos (26 registros)

| Campo | Presentes | % |
|---|---:|---:|
| `ad_id`, `title`, `url`, `collected_at`, `product_type`, `alcance` | 26 | 100 % |
| `price_raw`, `price_value`, `currency` | 25 | 96 % |
| `municipality`, `date_published`, `category` | 25 | 96 % |
| `power_raw`, `power_w` | 24 | 92 % |
| `brand` | 19 | 73 % |
| `garantia` | 8 | 31 % |
| `vida_util` | 6 | 23 % |
| `modelo` | 4 | 15 % |

El único valor ausente de `price_raw` (80011) es legítimo: el anuncio dice
"precio a convenir". El `category` y `date_published` que faltan corresponden al
**anuncio real** (Revolico no expone la fecha de publicación y el comando manual
no captura la categoría del sitio).

---

## 5. Duplicados

**Ninguno.** La deduplicación por URL (y, si falta, por `ad_id`) ya eliminó un
duplicado sintético del ejemplo `80001` que existía en el conjunto original.

---

## 6. Errores y anomalías detectadas

1. **Ejemplos mezclados con datos reales.** 25 de 26 filas son sintéticas.
   Aunque están etiquetadas, hay que **excluirlas** (`source != "ejemplo"`) para
   cualquier conclusión de mercado.
2. **El slug de la URL no coincide con el contenido.** La URL dice
   `594 paneles solares 720w jinko`, pero el anuncio real es **AIKO 660 W** con
   **720 paneles**. El slug está desactualizado; se documentó en `observaciones`.
3. **Precio ambiguo.** 145 USD no aclara si es **por panel** o **por el contenedor
   completo**. No se interpretó: se guardó tal cual.
4. **`alcance` derivado posiblemente incorrecto.** El limpiador asignó
   `alcance = "sistema completo"` al contenedor de 720 paneles. Un contenedor a
   granel encaja mejor en "varios paneles". Es una **derivación automática**, no
   un dato del anuncio.
5. **Garantía parcial.** El anuncio remite a "consultar las condiciones del
   proveedor" para la garantía del producto; solo la de rendimiento (30 años) es
   concreta.
6. **Precio en CUP no comparable.** Hay 1 precio en CUP (45 000) sin tasa de
   cambio; no debe promediarse con USD.
7. **Sin fecha de publicación real.** El único dato temporal del anuncio real es
   la última edición por el usuario, que **no** es la fecha de publicación.

---

## 7. Estadísticas básicas

> Calculadas sobre los 26 registros. **Advertencia:** al ser 25/26 sintéticos,
> describen sobre todo los **ejemplos**, no el mercado real. Úsese solo como
> comprobación técnica del pipeline.

**Por tipo de producto:** `panel solar` 17 · `kit solar` 4 · `inversor solar` 3 ·
`bateria solar` 2.

**Por moneda:** USD 25 · CUP 1.

**Precio en USD (n = 24):** media 1 213.12 · mediana 300 · mínimo 110 · máximo
9 500 · p25 225 · p75 1 112.5. (Incluye el ejemplo de 9 500 USD de un sistema de
8 kW, que eleva la media.)

**Precio en CUP (n = 1):** 45 000 (ejemplo).

**Por municipio:** Playa 5 · Boyeros 3 · Diez de Octubre, Marianao, Regla y Cerro
2 cada uno · Centro Habana, La Lisa, Guanabacoa, Habana Vieja, San Miguel del
Padrón, Cotorro, Habana del Este, Arroyo Naranjo y **Plaza de la Revolución** 1
cada uno · 1 sin municipio.

**Fechas de recopilación:** ejemplos 2026-10-15 (UTC); anuncio real 2026-10-16
(UTC).

---

## 8. Limitaciones de los datos

* **Muestra no representativa:** solo **1** anuncio real observado. No permite
  estimar precios ni tendencias del mercado.
* **Mayoría sintética:** el 96 % de las filas son de ejemplo.
* **Campos clave escasos incluso combinando todo:** `modelo` 15 %, `vida_util`
  23 %, `garantia` 31 %.
* **Sin serie temporal:** falta `fecha_publicacion` en el único anuncio real.
* **Fiabilidad = la de la fuente:** son **afirmaciones de los vendedores**, no
  datos verificados de forma independiente.
* **Sin conversión de moneda:** CUP y USD no se comparan.
* **Derechos de terceros:** los anuncios de Revolico están sujetos a sus
  Condiciones de uso (norma 12); el registro es una **transcripción manual de un
  anuncio de referencia**, no un scraping.

---

## 9. Cómo reproducir este informe

```bash
python main.py analyze
python -m pytest -q
# conteo por fuente y completitud:
python -c "import sys; sys.path.insert(0,'.'); from config import Config; from storage import load_csv; from collections import Counter; r=load_csv(Config.from_env().processed_csv_path); print('total', len(r)); print(Counter(x.get('source') for x in r))"
```

## 10. Recomendaciones

1. Analizar **solo** `source == "revolico"` (o excluir `ejemplo`) en cualquier
   estadística de mercado.
2. Incorporar más anuncios reales por la vía autorizada (`python main.py add` o
   `python main.py registrar`) antes de sacar conclusiones.
3. Si se requiere volumen, **pedir autorización por escrito** a la fuente
   (`python main.py solicitud --sitio revolico.com`) o usar datos abiertos de
   contexto (`python main.py opendata`).
