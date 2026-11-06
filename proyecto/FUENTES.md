# FUENTES.md — procedencia de cada dato

**Proyecto:** Mercado solar en La Habana — oferta anunciada, precio y compra real
**Fecha de elaboración:** 2026-11-05
**Regla aplicada:** ningún dato del proyecto fue inventado, simulado ni imputado. Cuando falta un dato se marca `NaN` y se documenta como limitación.

---

## 1. Fuentes locales (carpeta `data/raw/`)

| Archivo | Origen | SHA-256 | Campos usados | Notas |
|---|---|---|---|---|
| `telegram_anuncios.json` | Extracción propia del proyecto desde canales públicos de Telegram (`EquiposSolares`, `paneles_solares_cuba`), 352 anuncios | `5D6080F53F79BB56B77F51305B9BEEBA05F7EDB3659A4B03AE3529A8F6FAD446` | `id`, `canal`, `fecha_publicacion`, `categoria_producto`, `marca`, `potencia_w`, `precio`, `moneda`, `potencia_inversor_w`, `capacidad_ah`, `voltaje_nominal_v`, `garantia`, `municipio`, `url` | Es el único conjunto con fecha. El hash coincide con el documentado en `docs/informe_esquema_simplificado_telegram_v2.md` del proyecto original, lo que confirma que el archivo no fue alterado al copiarlo. |
| `revolico_anuncios.json` | Extracción propia desde Revolico (30 anuncios), heredada del pipeline original | `8674A947E50FF2FAB83ABA54EE38F486CC965AF007EEBC2CC68CC6153853763A` | `url`, `titulo`, `precio`, `potencia`, `marca`, `tipo_panel`, `municipio`, `moneda` | **No tiene fecha de publicación** → excluido de todas las series temporales. La categoría se infiere del título (variable derivada, declarada en el código). |
| `entrevistas.json` | Encuestas a compradores (35 compras), suministradas con el proyecto | `99A2520C6F96F6E532F8652C76722B6ED44E64C3A3CA572C003934C88BFC21D5` | `paneles[].id`, `marca`, `tipo_de_panel`, `potencia_por_panel`, `potencia_total`, `precio_por_panel`, `municipio`, `cantidad_de_paneles`, `lugar_de_adquisicion`, `garantia`, `vida_util`, `dispone_de_inversor`, `dispone_de_bateria` | **No tiene fecha de compra.** Tres registros (id 2, 7 y 20) traían nombres de columna alternativos; se unificaron conservando el valor (ver `colapsar_columnas` en `01_carga_limpieza.py`). Versión vigente: revisión del 2026-11-06 (ver §5). |

### Archivos deliberadamente **no** utilizados

| Archivo | Motivo |
|---|---|
| `data/ejemplo_anuncios.json` | 3 registros marcados como “datos de EJEMPLO, no extraídos del sitio” (URLs `example.org`). Usar datos sintéticos violaría la regla 2. |
| `output/paneles_solares.json` | 25 de sus 26 registros son sintéticos (`source = "ejemplo"`). Solo 1 es real y ya está contenido en Revolico. |
| `entrevistas_respaldo.jason.json` | Respaldo de 2 filas con esquema antiguo; subconjunto de `entrevistas.json`. |
| `*.backup*`, `*.v2_backup`, `*.original_backup` | Versiones históricas del mismo linaje; no aportan datos nuevos. |

---

## 2. Fuentes web oficiales descargadas (carpeta `data/fuentes/`)

### 2.1 ONEI — Balance de electricidad (tabla 10.14)

| Campo | Valor |
|---|---|
| **Sitio** | Oficina Nacional de Estadística e Información (ONEI), Cuba |
| **Página de origen** | http://www.onei.gob.cu/mineria-y-energia-0 |
| **URL exacta del archivo** | http://www.onei.gob.cu/sites/default/files/datos-estadisticos/2023-10/10.14-balance-de-electricidad.xlsx |
| **Archivo guardado** | `data/fuentes/onei_10.14_balance_electricidad.xlsx` (22 133 bytes) |
| **Copia de la página** | `data/fuentes/onei_mineria_y_energia.html` (50 023 bytes) |
| **Fecha de descarga** | 2026-11-05 |
| **SHA-256** | `6229453C80FFD13DAF69177F3D8B861E42042DC90992D396B1EB1FA252455AE7` |
| **Cobertura** | años 2019–2022, valores en GWh |
| **Campos usados** | `Fuentes (suministro total)`, `Importación (generación móvil)`, `Consumo total`, `Consumo residencial`, `Pérdidas` |
| **Uso en el proyecto** | Gráfico 01 y tabla `onei_variacion.csv`: variación del suministro eléctrico antes del auge del mercado solar |

> El archivo se lee con `openpyxl` desde el propio XLSX (tres bloques de dos años cada uno). No se transcribió ningún valor a mano.

### 2.2 Banco Mundial — indicadores de Cuba (datos abiertos)

| Campo | Valor |
|---|---|
| **Sitio** | World Bank Open Data (API v2) |
| **URL de origen** | https://api.worldbank.org/v2/country/CUB/indicator/EG.ELC.ACCS.ZS |
| **Archivo guardado** | `data/fuentes/opendata_banco_mundial.csv` (descargado por el pipeline original del proyecto con `opendata.py`) |
| **Fecha de recopilación (columna del propio CSV)** | 2026-10-15 |
| **Licencia** | CC BY 4.0 (indicada en el CSV) |
| **Indicadores incluidos** | `EG.ELC.ACCS.ZS` (acceso a electricidad), `EG.ELC.RNEW.ZS` (electricidad renovable), `EG.FEC.RNEW.ZS`, `EG.USE.PCAP.KG.OE`, `NY.GDP.PCAP.CD` |
| **Uso en el proyecto** | Contexto del capítulo 1 del notebook (acceso a electricidad = 100 %; electricidad renovable ≈ 4,8 % en 2021). No se usa para calcular ninguna cifra del mercado solar. |

---

## 3. Datos externos no verificados (auditoría 2026-11-07)

Los siguientes claims aparecieron en borradores del reportaje pero **no están documentados** en `FUENTES.md` ni en `data/fuentes/`. Se marcan como **no verificados** y se excluyen del reportaje final salvo que se documenten con URL y hash:

| Claim | Estado | Motivo |
|---|---|---|
| "6.700 GWh perdidos" (ministro de Energía) | **Inconsistente** | La ONEI registra −2.832 GWh (21 155 → 18 323 GWh, −13,4 %) entre 2019 y 2022. El claim de 6.700 GWh no coincide con la serie descargada. |
| "22 parques / 481 MW / 2.000 MW para 2028 / 750.000 t combustible" | No documentado | Sin fuente en el repo. |
| "Copextel, módulos 800-1.200 W, donaciones chinas, vida útil 20 años" | No documentado | Sin fuente en el repo. |
| "Granma" como fuente | No documentado | FUENTES.md solo registra ONEI y Banco Mundial. |
| "salario medio estatal" | Estimación blanda | No verificable. |

## 3b. Datos que **no** se pudieron obtener (y por eso el análisis se detiene ahí)

| Dato necesario | Para qué | Estado |
|---|---|---|
| Serie oficial de tipos de cambio (BCC) | Convertir los 7 anuncios en EUR y 2 en CUP a USD | **No descargada.** No se convirtió nada: esos 9 anuncios se excluyen de los análisis de precio y se reportan como `flag_moneda_no_usd`. Convertir con una tasa estimada sería fabricar el dato. |
| Radiación solar (INSMET) | Calcular energía generada (kWh) a partir de los kW | **No usada.** El proyecto mide precio por watt, no energía generada. |
| Horas de apagón / afectaciones (UNE, MINEM) | Estimar autonomía real de los sistemas comprados | **No disponible como serie descargable.** Por eso no se hizo el análisis de autonomía. |
| Fecha de compra en las entrevistas | Serie temporal de la demanda | **No existe en el instrumento.** `entrevistas.json` no registra fecha; ningún análisis temporal usa ese archivo. |
| Precio final de venta verificado | Validar el precio declarado | **No observable.** Se usa el precio declarado por el comprador, que es lo que el archivo contiene. |

---

## 4. Decisiones de limpieza documentadas

1. **Revolico `"000"`** → tratado como precio ausente (`NaN`), no como cero. El informe original del proyecto lo describe como “precio no capturado”.
2. **Precios < 20 USD** → marcados con `flag_precio_bajo` y excluidos de los estadísticos de precio (patrón compatible con un error de separador decimal: “1,150 USD” → 1,15). No se corrige el valor: se excluye.
3. **Potencia > 2 000 W en categoría “panel solar”** → marcada con `flag_potencia_imposible` y excluida de los cálculos por watt. Un panel comercial no supera ~700 W.
4. **Moneda ≠ USD** → marcada y excluida (ver §3).
5. **Municipios** → normalizados al catálogo oficial de los 15 municipios de La Habana (ya codificado en el proyecto original, `municipios.py`). Lo que no coincide queda `NaN`; no se asigna por defecto.
6. **Marcas** → 20 grafías observadas (MUST/Must/must/MUSt, LONGi/Longi/LONGI…) unificadas a 11 marcas canónicas.

---

## 5. Revisión del conjunto de entrevistas (2026-11-06)

El archivo `entrevistas.json` fue sustituido por una versión revisada. Cambios verificados por comparación registro a registro:

| Concepto | Antes | Después |
|---|---:|---:|
| Registros | 35 | 35 |
| Tamaño del archivo | 14 460 bytes | 17 558 bytes |
| Valores modificados | — | **61 en 21 registros** |
| Campos nuevos | — | `dispone_de_bateria`, `dispone_de_inversor` |
| Campo renombrado | `modelo` | `tipo_de_panel` |
| Garantías declaradas | 13 | 18 |
| Vida útil declarada | 16 | 14 |
| Compras con batería | no se registraba | **31 de 35** |
| Mediana pagada (USD/W) | 0,309 | **0,267** |

**Impacto en los resultados:** la brecha oferta-compra pasa de −15,0 % a **−26,6 %**; la garantía obtenida sube de 37,1 % a 51,4 %; el tamaño mediano de compra pasa de 3 a 4 paneles. Los gráficos 08, 09, 10, 11 y 12 se recalcularon con la nueva versión; se añadió el gráfico 12 para los dos campos nuevos.

Los valores anteriores quedan documentados aquí y en el historial de esta auditoría; **no se conserva copia del archivo previo dentro de `proyecto/`** para no duplicar fuentes.

