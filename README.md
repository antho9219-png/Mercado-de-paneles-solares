# Mercado solar en La Habana — recopilación y análisis de anuncios

Proyecto de ciencia de datos (nivel iniciación) que recopila, limpia y analiza
**anuncios públicos de venta de equipos solares** (paneles, kits, inversores,
baterías) ofrecidos en los municipios de **La Habana, Cuba**, para estudiar
precios, características técnicas y distribución geográfica de la oferta.

> ⚠️ **Los precios son ofertas publicadas, no ventas confirmadas.** Este proyecto
> no mide precios de transacción ni volumen de ventas. Tampoco convierte
> monedas: cada precio se analiza en su moneda original.

---

## 1. Objetivo del proyecto

* Recopilar información pública de anuncios de paneles solares en La Habana.
* Estructurar los datos en un conjunto tabular (CSV/JSON) reproducible.
* Limpiar y normalizar precios, potencias, municipios y campos técnicos.
* Analizar el mercado (precios, potencia, marcas, municipios, garantías, vida
  útil) mediante un notebook de análisis exploratorio.
* Hacerlo **respetando** las condiciones de uso del sitio y sin eludir ninguna
  medida de protección.

## 2. Fuente de datos

**Fuente principal:** [Revolico](https://www.revolico.com) (anuncios
clasificados en Cuba).

**Comprobaciones realizadas antes de implementar (fase 1):**

| Aspecto | Resultado |
| --- | --- |
| `robots.txt` (`https://www.revolico.com/robots.txt`) | `User-agent: *` / `Allow: /` (solo bloquea `/checkout/`, `/cdn-cgi/`, `/account`, `/auth`, `/favorites/`). |
| Condiciones de uso | Prohíben copiar/procesar/distribuir el texto de anuncios de terceros **sin autorización**. |
| Tecnología del sitio | Aplicación **Next.js**: los datos del listado viven en `<script id="__NEXT_DATA__">` (estado Apollo), no en el HTML visible. |
| Página de búsqueda | `https://www.revolico.com/search?q=<término>&page=<n>` funciona y devuelve anuncios con `province`/`municipality` resolubles. |
| Filtro por provincia | No se confirmó una URL de categoría por provincia (varias devuelven 404); se filtra por el campo `province` del anuncio. |

**Conclusión:** `robots.txt` permite el acceso a las páginas públicas, pero las
**condiciones de uso restringen la reproducción del contenido**. Por eso el
scraper está **desactivado por defecto** y el proyecto funciona principalmente
con **importación de datos obtenidos legítimamente** (`main.py import`).

## 3. Variables recopiladas

Las columnas de entrega (`data/raw` y `data/processed`) están **en español**:

| Columna (entrega) | Significado | ¿Derivada? |
| --- | --- | --- |
| `id_anuncio` | Identificador del anuncio | No |
| `titulo` | Título original | No |
| `descripcion` | Descripción original | No |
| `precio` | Precio tal como aparece | No |
| `precio_valor` | Precio numérico | Sí |
| `moneda` | Moneda indicada (no se convierte) | Sí/No |
| `potencia` | Potencia tal como aparece | No |
| `potencia_w` | Potencia normalizada a vatios | Sí |
| `marca` | Marca (solo marcas conocidas) | Sí |
| `modelo` | Modelo (extracción conservadora) | Sí |
| `tipo_producto` | panel / kit / inversor / batería / … | Sí |
| `alcance` | panel individual / varios paneles / sistema completo | Sí |
| `vida_util` | Vida útil declarada (con unidades) | Sí |
| `vida_util_anios` | Vida útil normalizada a años | Sí |
| `garantia` | Garantía anunciada (texto) | Sí |
| `ubicacion` | Municipio + provincia normalizados | Sí |
| `ubicacion_original` | Ubicación tal como aparecía | No |
| `provincia` | Provincia | No |
| `municipio` | Municipio de La Habana normalizado (o nulo) | Sí |
| `categoria` | Categoría del sitio | No |
| `fecha_publicacion` | Fecha de publicación (ISO 8601) | No |
| `url_anuncio` | URL pública del anuncio | No |
| `fecha_recopilacion` | Fecha/hora de recopilación (UTC) | Sí |
| `fuente` | `revolico`, `import` o `ejemplo` | No |

> El esquema interno del código usa nombres en inglés; la traducción a las
> columnas de entrega está centralizada en `storage.SPANISH_COLUMNS`.

## 4. Tecnologías utilizadas

* **Python 3.11+**
* `requests` — peticiones HTTP.
* `beautifulsoup4` — localización del bloque `__NEXT_DATA__`.
* `pandas` / `numpy` — tablas, limpieza y estadísticas.
* `matplotlib` + `seaborn` — gráficos (módulo `visualization.py` y notebook).
* `pytest` — pruebas automatizadas.
* `jupyter` / `nbformat` / `nbconvert` — notebook de análisis.

## 5. Instalación de dependencias

```bash
# 1) Crear y activar un entorno virtual
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# 2) Instalar dependencias
pip install -r requirements.txt
```

## 6. Instrucciones de ejecución

La configuración se lee de **variables de entorno** (valores por defecto
seguros). Copia `.env.example`, expórtalo en tu shell, o define las variables
necesarias.

```bash
# --- Diagnóstico (¿por qué no se recopilan anuncios reales?) ---
python main.py diagnose          # comprobaciones sin red (rápido, 0 peticiones)
python main.py diagnose --online # + robots.txt y estructura actual (2 peticiones)

# --- Importar datos obtenidos legítimamente (vía principal) ---
python main.py import --input data/examples/ejemplo_paneles_habana.csv
#   -> data/raw/paneles_solares_habana.csv
#   -> data/processed/paneles_solares_habana_limpio.csv
#   -> output/paneles_solares.csv | .json   (esquema interno)

# --- Plantilla CSV en español para aportar tus propios datos ---
python main.py template --output plantilla_anuncios.csv

# --- Analizar (estadísticas y calidad) ---
python main.py analyze                 # usa data/processed si existe
python main.py analyze --input otro.csv

# --- Generar gráficos PNG ---
python main.py visualize

# --- Scraping (solo con autorización; desactivado por defecto) ---
# En Linux/macOS:
SCRAPER_ENABLED=true AUTHORIZATION_CONFIRMED=true python main.py scrape --max-items 30
# En Windows (PowerShell):
#   $env:SCRAPER_ENABLED="true"; $env:AUTHORIZATION_CONFIRMED="true"
#   python main.py scrape --max-items 30

# --- Ejecutar las pruebas ---
python -m pytest -q

# --- Abrir el notebook ---
jupyter notebook notebooks/analisis_mercado_solar_habana.ipynb
```

**Códigos de salida de `scrape`:** `0` OK · `3` scraper no autorizado ·
`4` bloqueado por `robots.txt` · `5` error HTTP/formato.
**Códigos de salida de `diagnose`:** `0` sin errores · `1` hay algún error
que impediría la recopilación.

### Variables de entorno más útiles

`REQUEST_DELAY`, `MAX_PAGES`, `MAX_ITEMS`, `PAGE_LENGTH`, `FETCH_DETAILS`,
`MAX_DETAILS`, `RESPECT_ROBOTS`, `PROVINCE` (por defecto `La Habana`),
`DATA_DIR`, `OUT_DIR`, `LOG_DIR`, `SEARCH_TERMS`, `SCRAPER_ENABLED`,
`AUTHORIZATION_CONFIRMED` (ver `.env.example`).

### Diagnóstico: por qué se recopilan 0 anuncios reales

Si el programa devuelve **0 anuncios reales y solo datos de ejemplo**, ejecuta:

```bash
python main.py diagnose            # sin tocar la red
python main.py diagnose --online   # además verifica el sitio (2 peticiones)
```

El informe comprueba cinco hipótesis distintas y te dice cuál aplica:

| Hipótesis | Comprobación | Resultado típico |
|---|---|---|
| Variables de entorno mal configuradas | `gate:SCRAPER_ENABLED`, `gate:AUTHORIZATION_CONFIRMED` | **Sí influye:** ambas vienen `false` por defecto (opción deliberada). |
| Dependencias que faltan | `dep:requests`, `dep:beautifulsoup4`, `dep:pandas`, `dep:numpy` | Todas instaladas → `OK`. |
| Errores de conexión o respuestas HTTP | `online:search` (con `--online`) | `OK` (HTTP 200, respuesta recibida). |
| Cambios en la estructura HTML de Revolico | `online:parse` (con `--online`) | `OK` (parsea 100 anuncios; ~96 de La Habana). |
| Restricciones de acceso (robots / términos) | `online:robots.txt` | `/search` está **permitido** por `robots.txt`. |
| ¿Los datos actuales son reales? | `datos:fuente`, `datos:aviso` | `ejemplo=25` → todos son **sintéticos**, no reales. |

**Conclusión:** la red funciona, `robots.txt` permite el acceso, el parser
interpreta correctamente la estructura actual del sitio, y las dependencias
están completas. El **único** motivo por el que no se recopilan anuncios reales
es que el scraper está **desactivado por defecto** (`SCRAPER_ENABLED=false` y
`AUTHORIZATION_CONFIRMED=false`), una decisión de diseño alineada con los
términos de uso de Revolico.

**Cómo proceder:**

1. **Si tienes autorización / base legítima** para el acceso automatizado,
   define ambas variables y ejecuta `python main.py scrape --max-items 30`.
2. **Si no la tienes** (caso habitual), usa la vía de importación con datos que
   sí puedas tratar: `python main.py template` genera la plantilla con las
   columnas en español y `python main.py import --input <archivo>` la procesa.

Ninguna de estas opciones elude restricciones, y **ninguna inventa anuncios**:
lo que hay en `data/processed/` es lo que indica la columna `fuente`.

## 7. Estructura del repositorio

```
mercado-solar-cuba/
├── scraper/                       # Paquete de recopilación
│   ├── __init__.py
│   ├── revolico_scraper.py        # Cliente HTTP cortés (robots, pausas, errores)
│   └── collector.py               # Orquestación: filtro por provincia, dedup, límite
├── data/
│   ├── examples/                  # Datos de EJEMPLO (sintéticos, sí se versionan)
│   │   ├── ejemplo_paneles_habana.csv
│   │   └── README.md
│   ├── raw/                       # Datos crudos (generado; NO se versiona)
│   └── processed/                 # Datos limpios (generado; NO se versiona)
├── notebooks/
│   └── analisis_mercado_solar_habana.ipynb
├── tests/                         # 142 pruebas automatizadas
├── config.py                      # Esquema de campos y configuración
├── municipios.py                  # Normalización de los 15 municipios de La Habana
├── cleaner.py                     # Limpieza y derivación de campos
├── parser.py                      # Extracción del estado Next.js/Apollo
├── analysis.py                    # Duplicados, incompletos y estadísticas
├── storage.py                     # CSV/JSON (inglés interno y español de entrega)
├── diagnostics.py                 # Diagnóstico: ¿por qué 0 anuncios reales?
├── visualization.py               # Gráficos PNG
├── main.py                        # CLI: diagnose / template / scrape / import / analyze / visualize
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

> La estructura pedida (`scraper/revolico_scraper.py`, `data/raw`,
> `data/processed`, `notebooks/...`) se adoptó **adaptando** la organización
> previa del repositorio, conservando los módulos que ya funcionaban.

## 8. Metodología de limpieza

Definida en `cleaner.py` y `municipios.py`. Regla de oro: **nunca se inventan
valores**; si algo no se puede derivar con seguridad, queda como `None`.

* **Precios:** se separan los separadores de miles y decimales; se detecta la
  moneda por código (`USD`, `CUP`, `MLC`, `EUR`) y por símbolos no ambiguos
  (`€`). El símbolo `$` es ambiguo y **no** se asume USD.
* **Potencia:** se normaliza a vatios (`W`, `kW`); `kWh` se ignora por ser
  energía. ⚠️ En kits/sistemas, la potencia recogida puede ser la **del sistema
  completo**, no la de un panel: para no confundirlas se usa el campo `alcance`.
* **Marca y modelo:** la marca solo se asigna si aparece una marca conocida; el
  modelo se extrae de forma conservadora (marca + tesela con dígitos, ignorando
  potencias/voltajes). Por eso `modelo` suele quedar vacío.
* **Tipo de producto:** panel, kit, inversor, batería, controlador, estructura u
  «otro».
* **Alcance:** `panel individual`, `varios paneles`, `sistema completo` o
  `no determinado`; sirve para **no comparar** un panel con un kit.
* **Vida útil vs. garantía:** la vida útil solo se busca junto a la expresión
  «vida útil»; la garantía se busca junto a «garantía». No se confunden.
* **Municipios:** se normalizan a los **15 municipios de La Habana** ignorando
  acentos y variantes (`Vedado` → `Plaza de la Revolución`). «La Habana» **no**
  es un municipio: si la ubicación no basta, el municipio queda nulo y se
  conserva el texto original en `ubicacion_original`.
* **Duplicados:** se eliminan por URL normalizada y, si falta, por ID.
* **Registros incompletos:** no se descartan; se documentan.

## 9. Análisis exploratorio

En `notebooks/analisis_mercado_solar_habana.ipynb`:

1. Cantidad total de anuncios (y por tipo/alcance).
2. Distribución por municipio.
3. Distribución de precios (por moneda; solo paneles).
4. Precios según potencia nominal (correlación).
5. Frecuencia de marcas.
6. Frecuencia de modelos identificados.
7. Distribución de garantías anunciadas.
8. Análisis de la vida útil declarada.
9. Anuncios con información técnica incompleta.
10. Comparación de precios entre municipios (solo con ≥ 3 anuncios).

Cada gráfico lleva título, etiquetas y unidades. Las interpretaciones evitan
afirmaciones que los datos no permiten demostrar.

## 10. Limitaciones del scraping

* El sitio es una app Next.js: un cambio de estructura puede romper el parseo;
  los errores se registran sin abortar toda la ejecución. Puedes detectarlo con
  `python main.py diagnose --online` (comprueba robots.txt y la estructura actual).
* No se confirmó un filtro por provincia en la URL; se filtra por el campo
  `province` de cada anuncio.
* Las descripciones completas y muchos campos técnicos solo aparecen en la ficha
  del anuncio, por lo que se limita el número de fichas visitadas (`MAX_DETAILS`).
* `vida_util`, `garantia` y `modelo` solo se pueden derivar cuando el vendedor
  los escribe en el texto.

## 11. Consideraciones legales y éticas

* El scraper está **desactivado por defecto** y exige, de forma explícita,
  `SCRAPER_ENABLED=true` **y** `AUTHORIZATION_CONFIRMED=true`.
* Se respeta `robots.txt`; hay pausas entre peticiones y reintentos con espera.
* **No** se elude CAPTCHA, autenticación, bloqueos ni límites de tasa: ante
  `401`/`403`/`429` el proceso se detiene e informa.
* **No** se recopilan datos personales que no sean imprescindibles.
* Las condiciones de uso de Revolico restringen la reproducción del contenido de
  anuncios de terceros sin autorización; si no cuentas con autorización, usa la
  **vía de importación** con datos obtenidos legítimamente.
* Este repositorio **no** publica datos recopilados: `.gitignore` excluye
  `data/raw/` y `data/processed/` (solo se versionan los datos de ejemplo).

## 12. Advertencia sobre los precios

Los precios analizados son los **anunciados** por los vendedores. No
necesariamente corresponden a ventas realizadas, ni incluyen costos de envío,
instalación o garantía real. Las marcas, modelos, potencias, garantías y vidas
útiles son **declaraciones del vendedor**, no características verificadas de
forma independiente.

## 13. Publicación en GitHub

El flujo previsto (crear repo, commit y push) requiere que **Git esté instalado**
y que **tú autorices la publicación**.

```bash
# 1) Revisar el estado y los archivos
git status
git add .
git diff --cached --stat

# 2) Verificar que no se suben datos sensibles ni voluminosos (.gitignore lo cubre)
git status --ignored

# 3) Crear el commit (tras tu autorización)
git commit -m "feat: implementa scraping del mercado solar en La Habana"

# 4) Conectar el remoto y publicar (solo con tu autorización)
git remote add origin https://github.com/<usuario>/<repo>.git
git branch -M main
git push -u origin main
```

> **Nota:** en el entorno donde se desarrolló este proyecto, `git` **no estaba
> instalado**, por lo que **no se creó ningún commit ni se publicó nada**. Los
> comandos anteriores están listos para ejecutarse cuando lo autorices.

## 14. Pruebas

```bash
python -m pytest -q
```

Cubren precios, potencias, municipios, vida útil/garantía, modelo, alcance,
valores ausentes, duplicados, filtro por provincia, exportación en español,
el pipeline general y el **diagnóstico** (142 pruebas).

## 15. Datos de ejemplo

`data/examples/ejemplo_paneles_habana.csv` contiene **datos sintéticos**
(claramente etiquetados con `fuente=ejemplo`) para demostrar el flujo y ejecutar
las pruebas sin red. **No** son anuncios reales. Ver `data/examples/README.md`.
