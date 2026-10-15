# Investigación de fuentes: anuncios reales de paneles solares en La Habana

**Fecha de la investigación:** 2026-10-15
**Objetivo:** encontrar una fuente pública que permita obtener *anuncios reales*
de venta de paneles solares en La Habana mediante **API o descarga autorizada**,
sin inventar datos y sin confundir estadísticas energéticas con anuncios.

> Este documento no es asesoría legal. La situación puede cambiar: revisa siempre
> las condiciones y las licencias vigentes antes de reutilizar datos de terceros.

---

## 1. Pregunta y método

Se buscó una fuente que cumpla **las tres** condiciones:

1. que contenga **anuncios a nivel de listado** (precio, marca, modelo…), no
   estadísticas agregadas;
2. que permita **recolectar por API o descarga autorizada**;
3. que permita **reutilizar** los datos (licencia abierta o permiso).

Método: consulta de **fuentes primarias** (páginas de condiciones, `robots.txt`,
documentación de API y comprobaciones en vivo del API). La búsqueda web general
no estuvo disponible en este entorno (respuesta `HTTP 403`), por lo que se
priorizó el acceso directo a la documentación oficial de cada fuente.

## 2. Resultados

| Fuente | ¿Anuncios? | ¿API/descarga? | ¿Reutilizable? | Conclusión |
|---|---|---|---|---|
| **Revolico** (`revolico.com`) | Sí | `robots.txt` permite `/search` | **No** | Las condiciones prohíben copiar/procesar/distribuir contenido de terceros sin autorización escrita. |
| **Facebook Marketplace** y similares | Sí | Solo *Meta Content Library* | **No** | No hay API pública; la Content Library está restringida a investigadores aprobados. |
| **TecnoSolar Cuba** (`tecnosolarcuba.com`) | No (medianas) | No | **No** | Publica *medianas* de precios derivadas de anuncios; sin licencia ni API. |
| **Banco Mundial – Datos abiertos** | No | Sí (API pública) | **Sí** (CC BY 4.0) | Estadísticas agregadas por país. Comprobado en vivo. |
| **IRENA – Renewable Energy Statistics** | No | Sí (API PxWeb) | **Sí** (CC BY 4.0) | Capacidad/generación renovable. API comprobada en vivo. |
| **Global Solar Atlas** (Banco Mundial) | No | Descarga | **Sí** (CC BY 4.0) | Recurso solar y potencial fotovoltaico. |
| **UN Comtrade** | No | Sí (API) | Sí | Cuba **no** reporta la partida HS 8541 (paneles) en los periodos probados. |

### Evidencia consultada (2026-10-15)

* **Revolico – `robots.txt`** (`https://www.revolico.com/robots.txt`): `Allow: /`;
  solo se bloquean `/checkout/`, `/cdn-cgi/`, `/account`, `/auth`, `/favorites/`.
* **Revolico – Condiciones de uso**
  (`https://help.revolico.com/es/articles/7263759-condiciones-de-uso`): prohíben
  *copiar, procesar o distribuir* el texto y/o las imágenes de terceros sin
  **autorización previa**, y usar herramientas de publicación/renovación masiva
  sin **consentimiento escrito**.
* **Banco Mundial – API** (`https://api.worldbank.org/v2/country/CUB/...`):
  respuesta con datos reales para Cuba.
* **IRENA – PxWeb API** (`https://pxweb.irena.org/api/v1/en/`): responde y expone
  sus conjuntos estadísticos.
* **TecnoSolar Cuba** (`https://tecnosolarcuba.com/precios-paneles-solares-cuba`):
  sitio comercial cuyo *«termómetro»* publica medianas de «los anuncios de venta
  publicados», **no** los anuncios originales; sin API ni licencia abierta.

## 3. Conclusión

**No existe una fuente pública que permita obtener y reutilizar anuncios reales
de paneles solares en La Habana por API o descarga automatizada.** Todos los
sitios con anuncios a nivel de listado (Revolico, Facebook Marketplace…) exigen
autorización previa y por escrito, o restringen el acceso automatizado.

Las fuentes **legítimamente reutilizables** (Banco Mundial, IRENA, Global Solar
Atlas, UN Comtrade) contienen **estadísticas agregadas**, útiles como *contexto*
del mercado, pero **no son anuncios** y no tienen precio, marca ni modelo por
listado.

## 4. Alternativas disponibles (ordenadas por viabilidad)

1. **Transcripción manual de anuncios que observes como usuario normal.**
   Ya está implementada:
   ```bash
   python main.py add --interactive          # uno a uno
   python main.py template --anuncios        # varios de golpe (plantilla de 11 columnas)
   python main.py registrar --input plantilla_anuncios_reales.csv
   ```
   Cada fila exige **fuente verificable** (`url_fuente`); sin ella, se rechaza.
   No se inventa nada y los campos desconocidos quedan vacíos.

2. **Pedir autorización por escrito a la fuente.**
   El proyecto genera el borrador de la carta:
   ```bash
   python main.py solicitud --sitio revolico.com
   python main.py solicitud --sitio revolico.com --solicitante "..." --email "..." \
       --output solicitud_revolico.txt
   ```
   Si obtienes el permiso, podrás reutilizar esos datos y dejar constancia de la
   autorización.

3. **Solicitar acceso (de investigación) a la Meta Content Library** para
   Facebook Marketplace, si cumples los requisitos de investigador aprobado.

4. **Datos abiertos de contexto** (los reutilizables):
   ```bash
   python main.py opendata
   ```
   Estadísticas reales del Banco Mundial (CC BY 4.0). **No** son anuncios.

5. **Datos propios o encuestas**: registrar precios observados en tiendas/personas,
   con su fuente, usando el comando `add`/`registrar`.

> **Lo que no se hace:** no se scrapea sin autorización, no se elude ninguna
> medida de protección y **no se inventa ningún anuncio**. Por eso, hasta que se
> consigan datos reales, el proyecto muestra **0 anuncios reales** (solo datos
> abiertos de contexto y, en el flujo de ejemplo, registros sintéticos).

## 5. Cómo incorporar los anuncios reales (resumen)

| Paso | Comando |
|---|---|
| 1. Crear la plantilla | `python main.py template --anuncios` |
| 2. Rellenar una fila por anuncio (dejá vacío lo que no sepas) | — |
| 3. Añadir el `url_fuente` a cada fila (obligatorio) | — |
| 4. Registrar y deduplicar | `python main.py registrar --input plantilla_anuncios_reales.csv` |
| 5. Analizar | `python main.py analyze` |

* Los anuncios se guardan en `data/raw` y `data/processed`; **nunca** se mezclan
  con los datos abiertos.
* Los anuncios se deduplican por URL (y, si falta, por ID).
