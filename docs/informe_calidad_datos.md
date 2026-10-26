# Informe de Calidad de Datos

Fecha: 2026-10-26

## Conjuntos de datos

### Revolico (paneles_solares_completo.json)
- **Tamaño inicial:** 30 registros
- **Fuente:** Revolico (URLs revolico.com)
- **Ubicación:** Raíz del proyecto

### Telegram (data/telegram_paneles_habana.json)
- **Tamaño inicial:** 5 registros
- **Fuente:** Telegram (canales públicos)
- **Ubicación:** data/

## Auditoría Revolico

### Completitud
| Campo | Valores no nulos | % Completitud |
|---|---|---|
| titulo | 30 | 100% |
| url | 30 | 100% |
| provincia | 30 | 100% |
| precio | 28 | 93.3% |
| moneda | 28 | 93.3% |
| potencia | 25 | 83.3% |
| municipio | 28 | 93.3% |
| marca | 11 | 36.7% |
| tipo_panel | 17 | 56.7% |
| garantia | 7 | 23.3% |
| accesorios | 23 | 76.7% |
| estado | 3 | 10% |
| modelo | 0 | 0% |
| descripcion | 0 | 0% |

### Problemas detectados
- **Precios problemáticos:** 2 registros con precio "000" (no convertidos a 0)
- **Sin marca/modelo:** Mayoría sin marca (19/30) y ninguno con modelo
- **Sin descripción:** Todos sin descripción
- **Sin estado:** Mayoría sin estado
- **Kits mixtos:** Muchos anuncios son kits completos (inversor + baterías + paneles), no paneles individuales

### Categorías (clasificación)
| Categoría | Cantidad |
|---|---|
| Kits solares | 16 |
| Paneles individuales | 11 |
| Baterías | 3 |

### Duplicados
- **URLs únicas:** 30 de 30 (sin duplicados exactos por URL)
- **Duplicados potenciales:** Revisados manualmente, parecen únicos

### Distribución geográfica
- Mayoría en Centro Habana, Plaza, Playa, Cerro
- Todos en provincia La Habana

### Precios por moneda
- USD: mayoritariamente

## Integración Telegram-Revolico

**5 registros Telegram:**
- Todos con evidencia explícita de La Habana (algunos con municipio, otros solo provincia)
- Incluyen paneles individuales y 1 kit solar
- Fechas: nov 2025, sep/oct 2026
- Diferentes de Revolico (canales diferentes, estructura diferente)

**Recomendación:** Mantener separados por fuente. Añadir campo `fuente`. No mezclar como mismo registro sin evidencia.

## Limitaciones
- Revolico: datos de anuncios publicados, no representa mercado completo
- Telegram: solo 5 registros de 2 canales
- Muchos campos incompletos
- Kits vs paneles individuales difíciles de comparar
- Sin fechas completas en Revolico
- No mezclar monedas/precios entre categorías

## Recomendaciones para EDA
1. Separar análisis por categoría (panel individual vs kit)
2. No promediar precios de kits con paneles individuales
3. Considerar solo registros con precio válido y moneda
4. Usar `fuente` para distinguir origen
5. Trabajar con `data/revolico_limpio.json` y `data/telegram_paneles_habana.json` por separado o con marca de fuente
