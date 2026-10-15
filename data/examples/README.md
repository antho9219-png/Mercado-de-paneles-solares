# Datos de ejemplo (sintéticos)

> **Aviso importante:** los anuncios de este directorio son **datos de ejemplo
> inventados** con fines exclusivamente didácticos y de prueba. **No** son
> anuncios reales de Revolico ni de ninguna otra fuente, y **no** deben usarse
> para sacar conclusiones sobre el mercado real.

Sirven para:

* demostrar el flujo `import -> limpieza -> analisis -> notebook`;
* ejecutar las pruebas automatizadas sin depender de la red;
* tener datos suficientes para que el notebook genere gráficos.

La columna `source`/`fuente` vale `ejemplo`, de modo que siempre es posible
distinguir estos datos de los recopilados legítimamente.

## Archivos

| Archivo | Descripción |
| --- | --- |
| `ejemplo_paneles_habana.csv` | 26 anuncios de ejemplo centrados en La Habana (con un duplicado y algún valor ausente a propósito). |

## Cómo usarlos

```bash
python main.py import --input data/examples/ejemplo_paneles_habana.csv
```

Esto genera `data/raw/paneles_solares_habana.csv` y
`data/processed/paneles_solares_habana_limpio.csv` a partir del ejemplo.
Cuando tengas datos autorizados reales, repite el comando con tu propio
archivo y esos directorios se regenerarán.
