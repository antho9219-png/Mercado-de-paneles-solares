# ☀️ Mercado Solar en Cuba: crecimiento, oportunidades y futuro energético

Proyecto de **ciencia de datos** dedicado a **recopilar, organizar y analizar** información sobre la venta de paneles solares en Cuba, con especial atención a **La Habana**.

A partir de los anuncios públicos de venta, el proyecto busca describir el mercado —**precios, marcas, modelos, potencias, garantías, vida útil declarada y distribución geográfica de la oferta**— y explorar el papel que la energía solar podría desempeñar frente a la crisis energética, la necesidad de diversificar las fuentes de energía y la transición hacia alternativas más sostenibles desde el punto de vista ecológico.

> **Objetivo de fondo.** Comprender mejor el comportamiento del mercado solar cubano, detectar tendencias y explorar oportunidades para **hogares, empresas e instituciones**, siempre a partir de datos verificables y respetando las condiciones de uso de cada fuente.

> ⚠️ **Nota metodológica (importante).**
> Este proyecto **distingue con cuidado** entre:
> - los **datos observados** (lo que dicen literalmente los anuncios: precios publicados, marcas, potencias…), y
> - las **hipótesis y conclusiones** (interpretaciones que **todavía requieren investigación** y fuentes adicionales).
> Ninguna hipótesis se presenta aquí como un hecho demostrado.

---

## 🌱 El proyecto en breve

- **¿Qué hace?** Recopila anuncios públicos de venta de equipos solares, los limpia y normaliza en un conjunto de datos reproducible (CSV/JSON) y los analiza con estadísticas descriptivas y visualizaciones.
- **¿Dónde?** El foco geográfico es **La Habana, Cuba** (sus 15 municipios).
- **¿Para qué?** Para estudiar la oferta del mercado solar y explorar su potencial económico, energético y ambiental.
- **¿Cómo?** Con datos obtenidos por vías **legítimas**: transcripción manual, importación de datos aportados por el usuario o autorización por escrito del sitio. El proyecto **no** recopila automáticamente contenido de anuncios sin autorización.

> 🧭 **Precios = precios anunciados.** Los valores analizados son los que **publican los vendedores**, no necesariamente precios finales de venta. No incluyen envío, instalación ni verificación independiente de garantías o especificaciones.

---

## ❓ Preguntas que queremos responder

Estas preguntas guían la investigación. Algunas podrán responderse con los anuncios recopilados; **otras requerirán fuentes históricas, estadísticas oficiales o datos adicionales**.

### 📈 Crecimiento del mercado

- ¿Cuánto ha crecido el mercado de paneles solares en Cuba en comparación con hace cinco años?
- ¿Ha aumentado el interés de la población cubana por adquirir sistemas de energía solar?
- ¿Qué factores económicos, tecnológicos y energéticos podrían explicar el crecimiento de este mercado?
- ¿Qué tendencias pueden identificarse en la oferta de paneles solares?

> ⏳ Las preguntas sobre la evolución de los **últimos cinco años** no pueden responderse solo con anuncios actuales: requieren **series históricas, archivos de anuncios previos o estadísticas oficiales**.

### 🏠 Compradores y demanda

- ¿Quiénes son los principales compradores de paneles solares: hogares, empresas privadas o instituciones estatales?
- ¿Qué necesidades energéticas impulsan la adquisición de paneles solares?
- ¿Qué tipos de sistemas solares parecen tener mayor presencia en el mercado?
- ¿Qué barreras económicas dificultan el acceso a la energía solar en Cuba?

> 👥 La **identidad de los compradores** no puede deducirse de un anuncio de venta: haría falta información de demanda (encuestas, registros de importación, datos oficiales).

### 💰 Precios y características de los productos

- ¿Cuál es el precio promedio de los paneles solares anunciados en el mercado?
- ¿Qué marcas y modelos aparecen con mayor frecuencia?
- ¿Qué relación existe entre el precio, la potencia y la marca de los paneles?
- ¿Qué diferencias existen entre los productos nuevos y los usados, cuando esa información está disponible?
- ¿Qué garantías y vidas útiles declaran los vendedores?
- ¿Qué municipios de La Habana presentan mayor cantidad de anuncios?

### 🌍 Energía y ecología

- ¿Qué potencial tiene la energía solar para ayudar a reducir los efectos de la crisis energética en Cuba?
- ¿En qué medida podría contribuir a disminuir la dependencia de los combustibles fósiles?
- ¿Qué beneficios ambientales podrían obtenerse mediante una mayor utilización de la energía solar?
- ¿Qué desafíos económicos, técnicos y ambientales deben considerarse para impulsar su expansión?

### 🔮 Perspectivas futuras

- ¿Qué oportunidades de crecimiento podría tener el mercado solar cubano en los próximos años?
- ¿Qué tendencias actuales podrían ayudar a identificar oportunidades para hogares, empresas y emprendedores?
- ¿Qué información adicional sería necesaria para estimar el crecimiento real de la demanda nacional?

---

## 🎯 Objetivos del proyecto

- Recopilar y estructurar datos de anuncios de paneles solares.
- Analizar precios, potencias, marcas, modelos, garantías y vidas útiles declaradas.
- Examinar la distribución geográfica de la oferta.
- Identificar tendencias y patrones en los datos recopilados.
- Investigar fuentes complementarias que permitan estudiar la evolución del mercado durante los últimos cinco años.
- Explorar el potencial económico, energético y ambiental de la energía solar en Cuba.
- Desarrollar visualizaciones y conclusiones basadas en datos verificables.

---

## 🧭 Metodología

Las etapas previstas del trabajo son:

1. **Recopilación** de datos de anuncios públicos de venta, utilizando fuentes accesibles y respetando sus condiciones de uso.
2. **Limpieza y normalización** de los datos.
3. **Identificación y tratamiento** de anuncios duplicados, valores faltantes e inconsistencias.
4. **Análisis exploratorio** de los datos.
5. **Elaboración de gráficos y estadísticas descriptivas.**
6. **Contraste** de los resultados con estadísticas oficiales y fuentes históricas, cuando estén disponibles.
7. **Interpretación** de los resultados y elaboración de conclusiones.

> 📌 **Sobre los precios:** se analizan **precios anunciados**, no necesariamente precios finales de venta. Tampoco se asume que un anuncio publicado equivalga a una venta realizada.

### Regla de oro de la limpieza

**Nunca se inventan datos.** Cuando un campo no puede derivarse con seguridad, se deja **vacío** y, si procede, se conserva el texto original del anuncio. Las columnas derivadas (por ejemplo, un precio numérico o una potencia en vatios) se calculan solo a partir de lo que el vendedor escribió.

---

## 🛠️ Herramientas

El proyecto está desarrollado en **Python** y utiliza las siguientes tecnologías:

| Herramienta | Para qué se usa |
| --- | --- |
| **Python 3.11+** | Lenguaje base del proyecto. |
| `requests` | Peticiones HTTP (acceso cortés y respetuoso a las fuentes). |
| `beautifulsoup4` | Localización del bloque de datos del listado en el HTML. |
| `pandas` / `numpy` | Tablas, limpieza, normalización y estadísticas. |
| `matplotlib` | Generación de gráficos (módulo `visualization.py` y notebook). |
| `seaborn` | Gráficos estadísticos del notebook (opcional). |
| `jupyter` / `nbformat` | Notebook de análisis exploratorio. |
| `pytest` | Pruebas automatizadas. |
| Módulos estándar (`argparse`, `logging`, `csv`, `json`, `pathlib`) | Interfaz de línea de comandos, registro de actividad y entrada/salida de datos. |

> ℹ️ Estas son las herramientas **realmente utilizadas** por el proyecto según `requirements.txt` y el código. No se listan tecnologías que aún no estén integradas.

---

## 📊 Estado del proyecto

El proyecto se encuentra **en desarrollo**. Sus resultados dependerán de la **disponibilidad, la calidad y la representatividad** de los datos recopilados.

- El repositorio incluye la **infraestructura de datos** (importación, limpieza, normalización, análisis y visualización) y **datos de ejemplo** con fines de demostración y pruebas.
- La incorporación de **anuncios reales** se realiza únicamente por vías autorizadas (registro manual, importación de datos aportados o autorización por escrito de la fuente).
- Por privacidad y respeto a las condiciones de uso, **el repositorio no publica datos recopilados**: `data/raw/` y `data/processed/` están excluidos mediante `.gitignore`.
- Las conclusiones se irán construyendo **a medida que se amplíe y valide** el conjunto de datos.

---

## 📦 Instalación

```bash
# 1) Crear y activar un entorno virtual
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# 2) Instalar las dependencias
pip install -r requirements.txt
```

La configuración se lee de **variables de entorno** (con valores por defecto seguros). Puedes basarte en `.env.example`.

---

## 🚀 Uso rápido (línea de comandos)

```bash
# Diagnóstico: ¿por qué se recopilan (o no) anuncios reales?
python main.py diagnose            # sin red
python main.py diagnose --online   # + comprueba el sitio (2 peticiones)

# Catálogo de fuentes y su estado legal de reutilización
python main.py fuentes

# Solicitud de autorización por escrito (genera un borrador; NO envía nada)
python main.py solicitud

# Datos abiertos y reutilizables (contexto, NO anuncios)
python main.py opendata            # -> data/raw/opendata_banco_mundial.csv

# Registro manual de un anuncio (vía autorizada)
python main.py add --interactive

# Plantilla + registro de varios anuncios reales (valida fuente y evita duplicados)
python main.py template --anuncios
python main.py registrar --input plantilla_anuncios_reales.csv

# Importación de datos aportados legítimamente
python main.py import --input data/examples/ejemplo_paneles_habana.csv

# Análisis (estadísticas y calidad de los datos)
python main.py analyze

# Generación de gráficos PNG
python main.py visualize

# Pruebas automatizadas
python -m pytest -q
```

---

## 🗂️ Estructura del repositorio

```
mercado-solar-cuba/
├── scraper/                        # Paquete de recopilación (uso cortés y autorizado)
│   ├── __init__.py
│   ├── revolico_scraper.py         # Cliente HTTP respetuoso (robots, pausas, errores)
│   └── collector.py                # Filtro por provincia, deduplicación y límites
├── data/
│   ├── examples/                   # Datos de EJEMPLO (sintéticos, sí se versionan)
│   ├── raw/                        # Datos crudos (generado; NO se versiona)
│   └── processed/                  # Datos limpios (generado; NO se versiona)
├── notebooks/
│   └── analisis_mercado_solar_habana.ipynb
├── docs/
│   ├── investigacion_fuentes_anuncios.md   # Fuentes investigadas y alternativas
│   └── informe_estado_datos.md             # Informe de estado y calidad de los datos
├── tests/                          # Pruebas automatizadas
├── config.py                       # Esquema de campos y configuración
├── municipios.py                   # Normalización de los 15 municipios de La Habana
├── cleaner.py                      # Limpieza y derivación de campos
├── manual.py                       # Registro manual de un anuncio (vía autorizada)
├── anuncios.py                     # Plantilla + registro de anuncios reales
├── permisos.py                     # Borrador de la carta de autorización
├── sources.py                      # Catálogo de fuentes y su estado legal
├── opendata.py                     # Datos abiertos reutilizables (Banco Mundial)
├── parser.py                       # Extracción del estado de la página
├── analysis.py                     # Duplicados, incompletos y estadísticas
├── storage.py                      # Entrada/salida CSV/JSON (esquema de entrega)
├── diagnostics.py                  # Diagnóstico de la recopilación
├── visualization.py                # Gráficos PNG
├── main.py                         # Interfaz de línea de comandos (CLI)
├── plantilla_anuncios_reales.csv   # Plantilla de registro manual (11 columnas)
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧾 Variables recopiladas

Las columnas de entrega (`data/raw` y `data/processed`) están **en español**:

| Columna | Significado | ¿Derivada? |
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
| `vida_util` | Vida útil declarada (con unidades) | No |
| `vida_util_anios` | Vida útil normalizada a años | Sí |
| `garantia` | Garantía anunciada (texto) | No |
| `ubicacion` | Municipio + provincia normalizados | Sí |
| `ubicacion_original` | Ubicación tal como aparecía | No |
| `provincia` | Provincia | No |
| `municipio` | Municipio de La Habana normalizado (o nulo) | Sí |
| `categoria` | Categoría del sitio | No |
| `fecha_publicacion` | Fecha de publicación (ISO 8601) | No |
| `url_anuncio` | URL pública del anuncio | No |
| `fecha_recopilacion` | Fecha/hora de recopilación (UTC) | Sí |
| `fuente` | Origen del dato (`revolico`, `import`, `registro_manual`, `ejemplo`) | No |
| `observaciones` | Observaciones del investigador (texto libre) | No |

> 🔎 La columna `fuente` permite **distinguir siempre** los datos reales de los de ejemplo.

---

## ✅ Calidad, límites y advertencias

- **Los precios son anunciados**, no precios de transacción confirmados. Tampoco se convierten monedas: cada precio se analiza en su moneda original.
- **Marcas, modelos, potencias, garantías y vidas útiles** son **declaraciones del vendedor**, no características verificadas de forma independiente.
- Algunos campos (por ejemplo, `vida_util`, `garantia` o `modelo`) solo pueden derivarse cuando el vendedor los escribe en el texto del anuncio.
- **Vida útil y garantía** son conceptos distintos: se identifican por separado y no se confunden.
- **`alcance`** evita comparaciones incorrectas entre un panel individual y un sistema completo.
- Los **registros incompletos no se descartan**: se documentan para transparentar la calidad de los datos.
- Una fuente de **datos abiertos** puede aportar **contexto**, pero no contiene anuncios ni precios de paneles.

---

## ⚖️ Consideraciones legales y éticas

- El proyecto **no recopila automáticamente** anuncios cuando las condiciones de uso de la fuente lo prohíben; la recopilación automatizada está **desactivada por defecto**.
- Se respeta `robots.txt`, se aplican pausas entre peticiones y **no se elude** ninguna medida de protección, autenticación ni límite de tasa.
- Las vías autorizadas para conseguir anuncios reales son: la **transcripción manual**, la **importación** de datos aportados legítimamente y la **autorización por escrito** de la fuente (el borrador de esa solicitud lo genera el propio proyecto).
- El repositorio **no publica datos recopilados** de terceros (`data/raw/` y `data/processed/` están excluidos del control de versiones).

### Fuentes y su estado de reutilización

`python main.py fuentes` muestra el catálogo completo. Resumen:

| Fuente | Tipo | ¿Anuncios? | Reutilización | Acceso automatizado |
| --- | --- | --- | --- | --- |
| Revolico | clasificados | Sí | No sin autorización escrita | No permitido |
| Facebook Marketplace y similares | clasificados | Sí | No sin permiso | No (acceso restringido) |
| TecnoSolar Cuba (termómetro de precios) | editorial-comercial | No (medianas) | No sin permiso | No recomendado |
| Banco Mundial – datos abiertos | datos abiertos | No | Sí (CC BY 4.0) | Sí (API pública) |
| IRENA – estadísticas | datos abiertos | No | Sí (CC BY 4.0) | Sí (API PxWeb) |
| Global Solar Atlas | datos abiertos | No | Sí (CC BY 4.0) | Descarga |
| UN Comtrade | datos abiertos | No | Sí | Sí (API) |
| Prensa especializada | editorial | No | No sin permiso | No recomendado |

> **Conclusión:** ninguna fuente de **anuncios** permite reutilizar su contenido sin autorización previa; las fuentes **abiertas** sí pueden reutilizarse, pero contienen **estadísticas agregadas**, no listados con precio, marca o modelo.

> 📄 Investigación detallada de fuentes y alternativas legítimas: [`docs/investigacion_fuentes_anuncios.md`](docs/investigacion_fuentes_anuncios.md). Informe de estado y calidad de los datos: [`docs/informe_estado_datos.md`](docs/informe_estado_datos.md).

---

## 🧪 Pruebas

El proyecto incluye **229 pruebas automatizadas** que cubren la limpieza y derivación de campos, la normalización de municipios, la detección de duplicados e incompletos, el catálogo de fuentes, el registro manual y por plantilla, los datos abiertos y la interfaz de línea de comandos.

```bash
python -m pytest -q
```

---

## 🤝 Principios del proyecto

1. **Datos verificables:** no se inventan valores ni resultados.
2. **Transparencia:** se distingue siempre el dato observado de la interpretación.
3. **Respeto por las fuentes:** se cumple con las condiciones de uso y las normas legales.
4. **Utilidad pública:** el análisis busca aportar información útil para hogares, empresas e instituciones interesadas en la energía solar en Cuba.
