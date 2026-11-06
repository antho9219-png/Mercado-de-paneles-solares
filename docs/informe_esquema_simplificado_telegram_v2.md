# Informe de simplificación de esquema — telegram_paneles_habana_ampliado_v2.json

**Fecha:** 2026-10-30

## Resumen

Se eliminaron exactamente **7 claves autorizadas** de todos los registros del JSON v2 y del código
del pipeline de Telegram que las generaba o validaba. No se eliminó ningún registro ni ningún otro
campo. Todos los valores restantes se conservaron exactamente como estaban.

## Campos eliminados (7)

| Campo | Motivo |
|-------|--------|
| `descripcion` | Texto completo del anuncio; no es necesario para análisis estadístico |
| `titulo` | Siempre era `null` (100% nulos, sin evidencia en Telegram) |
| `potencia` | Duplicado exacto de `potencia_w` (mismos 214 valores no nulos) |
| `cantidad` | Duplicado de `cantidad_paneles` (ambos eliminados) |
| `cantidad_paneles` | Redundante para el análisis decidido |
| `potencia_por_panel_w` | 100% nulos (nunca se pobló con evidencia) |
| `potencia_total_w` | 100% nulos (nunca se pobló con evidencia) |

## Registros y claves

| Métrica | Antes | Después |
|---------|-------|---------|
| Registros | 352 | 352 |
| Claves por registro | 49 | 42 |
| Duplicados por `id` | 0 | 0 |
| Valores de claves eliminados (7 × 352) | — | 2 464 |
| Registros con claves eliminadas restantes | — | 0 |

## Verificación de integridad

- JSON válido antes y después (cargado con `json.load()`).
- Verificación campo a campo: cada registro conservó exactamente los mismos valores en
  las 42 claves restantes (comparación dict a dict, registro por registro).
- SHA-256 antes: `38DAF831892A9A177167141DE77276CDE56ACA1AD6390B75347E2971EDF73638`
- SHA-256 después: `5D6080F53F79BB56B77F51305B9BEEBA05F7EDB3659A4B03AE3529A8F6FAD446`
- Backup previo: `data/telegram_paneles_habana_ampliado_v2.json.backup_pre_esquema_simplificado_20261030_*`

## Completitud de los campos restantes (352 registros)

| Campo | No nulos | % No nulos | % Nulos |
|-------|----------|------------|---------|
| `id` | 352 | 100.0% | 0% |
| `canal` | 352 | 100.0% | 0% |
| `message_id` | 352 | 100.0% | 0% |
| `telegram_message_id` | 352 | 100.0% | 0% |
| `url` | 352 | 100.0% | 0% |
| `url_mensaje` | 352 | 100.0% | 0% |
| `url_anuncio` | 352 | 100.0% | 0% |
| `fuente` | 352 | 100.0% | 0% |
| `fecha_publicacion` | 352 | 100.0% | 0% |
| `fecha_extraccion` | 352 | 100.0% | 0% |
| `categoria` | 352 | 100.0% | 0% |
| `categoria_producto` | 352 | 100.0% | 0% |
| `tipo` | 352 | 100.0% | 0% |
| `clasificacion_geografica` | 352 | 100.0% | 0% |
| `estado` | 352 | 100.0% | 0% (`desconocido` when not evidenced) |
| `potencia_w` | 214 | 60.8% | **39.2%** |
| `precio` | 186 | 52.8% | **47.2%** |
| `moneda` | 186 | 52.8% | **47.2%** |
| `observaciones` | 107 | 30.4% | 69.6% |
| `marca` | 98 | 27.8% | **72.2%** |
| `capacidad_ah` | 64 | 18.2% | 81.8% |
| `potencia_inversor_w` | 74 | 21.0% | 79.0% |
| `voltaje_nominal_v` | 61 | 17.3% | 82.7% |
| `provincia` | 58 | 16.5% | 83.5% (null = sin localidad especificada) |
| `tipo_inversor` | 56 | 15.9% | 84.1% |
| `tipo_bateria` | 41 | 11.6% | 88.4% |
| `garantia` | 42 | 11.9% | 88.1% |
| `municipio` | 18 | 5.1% | 94.9% |
| `localidad` | 18 | 5.1% | 94.9% |
| `tipo_panel` | 31 | 8.8% | 91.2% |
| `energia_kwh` | 28 | 8.0% | 92.0% |
| `modelo` | 13 | 3.7% | **96.3%** |
| `vida_util` | 3 | 0.9% | **99.1%** |
| `incluye_paneles` | 0 | 0.0% | **100%** |
| `incluye_bateria` | 0 | 0.0% | **100%** |
| `incluye_inversor` | 0 | 0.0% | **100%** |
| `componentes_incluidos` | 0 | 0.0% | **100%** |
| `precio_sistema` | 0 | 0.0% | **100%** |
| `marca_bateria` | 0 | 0.0% | **100%** |
| `modelo_bateria` | 0 | 0.0% | **100%** |
| `marca_inversor` | 0 | 0.0% | **100%** |
| `modelo_inversor` | 0 | 0.0% | **100%** |

## Campos con mayor porcentaje de valores null (candidatos a decidir)

**100% nulos (10 campos):** `incluye_paneles`, `incluye_bateria`, `incluye_inversor`,
`componentes_incluidos`, `precio_sistema`, `marca_bateria`, `modelo_bateria`,
`marca_inversor`, `modelo_inversor` y (antes de esta simplificación) `titulo`.

> Nota: los 9 primeros NO se eliminaron porque no están en tu lista autorizada;
> requieren tu decisión (ver "Problemas pendientes").

**>90% nulos:** `vida_util` (99.1%), `modelo` (96.3%), `municipio`/`localidad` (94.9%).

** Moderada:** `tipo_bateria` (88.4%), `garantia` (88.1%), `tipo_inversor` (84.1%),
`capacidad_ah`, `voltaje_nominal_v`, `potencia_inversor_w` (~80%).

## Resultado de las pruebas automatizadas

- Suite completa: **270 passed, 0 failed** (`python -m pytest`).
- Pruebas nuevas/actualizadas para el esquema simplificado:
  - El parser no emite ninguna de las 7 claves eliminadas y conserva `potencia_w`.
  - El validador rechaza registros que contengan claves obsoletas (`REMOVED_KEYS`).
  - El JSON v2 no contiene ninguna de las 7 claves y conserva `potencia_w`, `id`,
    `canal`, `url_mensaje` y `clasificacion_geografica`.
  - Regla de suficiencia adaptada: sin `descripcion`, un anuncio requiere marca o
    modelo, o bien una oferta concreta (precio + categoría).

## Código actualizado

| Archivo | Cambio |
|---------|--------|
| `scraper/telegram_parser.py` | El registro generado ya no incluye las 5 claves que emitía (`descripcion`, `titulo`, `potencia`, `cantidad`, `cantidad_paneles`). Conserva `potencia_w`. |
| `scraper/telegram_validator.py` | Constante `REMOVED_KEYS` + `removed_keys_present()` / `is_simplified_schema()`; `validate()` rechaza registros con claves obsoletas; suficiencia adaptada al nuevo esquema. |
| `extraer_telegram_v2.py` | Mapeo de salida sin las 7 claves; informe de nulos sin campos eliminados. |
| `extract_telegram_habana.py` | Mapeo v1 actualizado (`potencia_w` en lugar de `potencia`; sin `cantidad`/`descripcion`). |
| `ampliar_extraccion_telegram.py` | Mapeo v1 ampliado actualizado (igual criterio). |
| `generar_telegram_mejorado.py` | Mapeo actualizado (igual criterio). |
| `tests/test_telegram_parser.py` | Adaptado + nueva prueba de esquema simplificado. |
| `tests/test_telegram_habana_filters.py` | Adaptado + pruebas de claves obsoletas y de regla de suficiencia. |
| `tests/test_telegram_ampliacion_v2.py` | Adaptado + pruebas del JSON v2 (sin claves eliminadas, con `potencia_w`). |
| `docs/informe_ampliacion_telegram_v2.md` | Sección de actualización de esquema añadida. |

## Excepciones (decisión de alcance)

Los scripts del **pipeline de Revolico** (`revolico_json.py`, `revolico_registrar.py`,
`storage.py`, `scrape_revolco_ia_full.py`, `analysis.py`, `audit_revolico.py`) usan claves
con nombres similares (`potencia`, `cantidad`, `descripcion`, `titulo`), pero pertenecen a
otro dataset con su propio esquema. No se modificaron para no romper ese pipeline.
`informe_calidad_telegram.py` y `reprocesar_5_registros.py` analizan los datasets v1
históricos (que conservan el esquema antiguo y sus copias de seguridad). No se modificaron.

## Sin re-extracción

No se volvió a extraer datos de Telegram: la simplificación se aplicó sobre el archivo
existente, que permanece íntegro salvo las 7 claves eliminadas.
