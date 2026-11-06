# Informe de Ampliación Telegram v2

**Fecha de ejecución:** 2026-10-28T19:09:41.650811+00:00

## Canales procesados
- EquiposSolares
- paneles_solares_cuba

## Métricas de extracción
- **Mensajes recuperados (total accesibles):** 2716
- **Mensajes analizados:** 2716
- **Anuncios candidatos (con producto relevante):** 986
- **Anuncios válidos encontrados (únicos):** 352
- **Anuncios clasificados como La Habana:** 58
- **Anuncios sin localidad especificada:** 850
- **Anuncios excluidos por mencionar otra provincia:** 70
- **Mensajes que requieren revisión manual:** 0
- **Duplicados confirmados:** 0
- **Posibles duplicados:** 0 (registrados en proceso de deduplicación)

## Categorías de productos encontradas
- batería: 79
- inversor: 38
- kit solar: 42
- panel solar: 193

## Cantidad de registros con valores nulos por campo
| Campo | Nulos | Total | % Nulos |
|-------|-------|-------|---------|
| marca | 254 | 352 | 72.2% |
| modelo | 339 | 352 | 96.3% |
| potencia_w | 138 | 352 | 39.2% |
| precio | 166 | 352 | 47.2% |
| moneda | 166 | 352 | 47.2% |
| municipio | 334 | 352 | 94.9% |
| localidad | 334 | 352 | 94.9% |
| garantia | 310 | 352 | 88.1% |
| vida_util | 349 | 352 | 99.1% |
| tipo_panel | 321 | 352 | 91.2% |
| tipo_bateria | 311 | 352 | 88.4% |
| capacidad_ah | 288 | 352 | 81.8% |
| voltaje_nominal_v | 291 | 352 | 82.7% |
| energia_kwh | 324 | 352 | 92.0% |
| tipo_inversor | 296 | 352 | 84.1% |
| potencia_inversor_w | 278 | 352 | 79.0% |
| estado | 0 | 352 | 0.0% |
| descripcion | 0 | 352 | 0.0% |
| titulo | 352 | 352 | 100.0% |

## Errores de extracción y limitaciones de acceso
- Sin errores de acceso reportados
- Extracción basada en texto completo de mensajes
- Solo recursos accesibles analizados; sin inventar información
- Enfoque en mensajes con evidencia explícita

## Métodos utilizados para validar los resultados
- Clasificación geográfica por mención explícita de La Habana/municipios vs otras provincias cubanas
- Detección de duplicados por combinación (canal, message_id), URL y análisis de contenido
- Validación de suficiencia: requiere marca/descripción y algún dato técnico/precio
- Filtrado: exclusión de preguntas/informativos, enfoque en anuncios de venta
- Normalización de unidades/marcas sin inferencias
- Verificación de valores permitidos para clasificacion_geografica

## Copias de seguridad creadas (verificables)
- C:\Users\Ramsés\Documents\proyecto cd\data\telegram_paneles_habana.json.backup_v2_20261028_150845
- C:\Users\Ramsés\Documents\proyecto cd\data\telegram_paneles_habana_ampliado.json.backup_v2_20261028_150845
- C:\Users\Ramsés\Documents\proyecto cd\data\telegram_paneles_habana_mejorado.json.backup_v2_20261028_150845

## Notas
- Los archivos originales NO fueron sobrescritos. Se generaron nuevos archivos de salida.
- Se distingue entre mensajes recuperados, anuncios candidatos y anuncios válidos.
- No se inventaron datos; valores ausentes se marcan como null.

## Actualización de esquema (2026-10-30)

El esquema de `data/telegram_paneles_habana_ampliado_v2.json` fue simplificado. Se eliminaron las claves
`descripcion`, `titulo`, `potencia`, `cantidad`, `cantidad_paneles`, `potencia_por_panel_w` y `potencia_total_w`
de todos los registros y del código que las genera/valida (`scraper/telegram_parser.py`,
`scraper/telegram_validator.py`, `extraer_telegram_v2.py`). `potencia_w` es el único campo de potencia general.
Se conservaron los 352 registros y todos los demás campos sin alterar sus valores.
Los recuentos de nulos de las tablas anteriores a esta fecha corresponden al esquema previo de 49 claves.
Detalle completo en `docs/informe_esquema_simplificado_telegram_v2.md`.
