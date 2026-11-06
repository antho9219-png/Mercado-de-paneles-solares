from fpdf import FPDF

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Helvetica", "", 11)

def titulo(t):
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, t, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(3)

def sec(t):
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, t, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)

def para(s):
    pdf.multi_cell(0, 7, s)
    pdf.ln(2)

def bullet(s):
    pdf.multi_cell(0, 7, "- " + s)
    pdf.ln(1)

pdf.add_page()
titulo("Informe Tecnico del Proyecto")
para("Mercado de paneles solares en La Habana: analisis de oferta, precio y compra real a partir de fuentes heterogeneas. Proyecto reproducible con reglas estrictas de no imputacion ni invencion de datos.")

sec("1. Definicion del problema")
para("El mercado solar cubano carece de datos oficiales unificados. Para cuantificar la transparencia, el precio y la compra real, se diseno un pipeline de ciencia de datos sobre anuncios de Telegram y Revolico (382 anuncios) y 35 entrevistas a compradores, complementado con la serie oficial de la ONEI (2019-2022) y datos abiertos del Banco Mundial. El reto principal fue la disponibilidad y calidad de los datos: no existen datasets limpios del mercado cubano de paneles solares.")

sec("2. Fuentes de datos")
para("Fuentes locales (data/raw/):")
bullet("telegram_anuncios.json: 352 anuncios con fecha (2022-06 a 2026-10). Campos: id, canal, fecha_publicacion, categoria_producto, marca, potencia_w, precio, moneda, potencia_inversor_w, capacidad_ah, voltaje_nominal_v, garantia, municipio, url. Unico conjunto con fecha.")
bullet("revolico_anuncios.json: 30 anuncios sin fecha. Campos: url, titulo, precio, potencia, marca, tipo_panel, municipio, moneda. La categoria se infiere del titulo (variable derivada).")
bullet("entrevistas.json: 35 compras sin fecha de compra. Campos: paneles[].id, marca, tipo_de_panel, potencia_por_panel, potencia_total, precio_por_panel, municipio, cantidad_de_paneles, lugar_de_adquisicion, garantia, vida_util, dispone_de_inversor, dispone_de_bateria. Tres registros (id 2, 7 y 20) traian nombres de columna alternativos; se unificaron conservando el valor (colapsar_columnas).")
para("Fuentes web oficiales (data/fuentes/):")
bullet("ONEI - Balance de electricidad (tabla 10.14): 2019-2022, GWh. Campos: Fuentes (suministro total), Importacion (generacion movil), Consumo total, Consumo residencial, Perdidas. Leido con openpyxl (3 bloques de dos anos).")
bullet("Banco Mundial - Open Data: indicadores EG.ELC.ACCS.ZS, EG.ELC.RNEW.ZS, EG.FEC.RNEW.ZS, EG.USE.PCAP.KG.OE, NY.GDP.PCAP.CD. Solo contexto (acceso a electricidad = 100 %; renovable ~4,8 % en 2021). No se usa para calcular cifras del mercado solar.")
para("Archivos deliberadamente no utilizados: ejemplo_anuncios.json (3 registros sinteticos), output/paneles_solares.json (25 de 26 sinteticos), entrevistas_respaldo.jason.json (subconjunto), backups historicos.")

sec("3. Recoleccion y limpieza")
para("Reglas no negociables:")
bullet("No se inventa ni se imputa nada. Lo ausente queda NaN y se reporta.")
bullet("No se convierten monedas sin serie oficial de tipos de cambio: 9 anuncios (7 EUR, 2 CUP) quedan fuera de los analisis de precio (flag_moneda_no_usd).")
bullet("Los errores se marcan, no se borran: flag_sin_precio, flag_precio_bajo, flag_potencia_imposible, flag_moneda_no_usd.")
bullet("No se usan archivos sinteticos.")
bullet("Toda fuente web queda descargada y documentada en FUENTES.md con URL, fecha y SHA-256.")
para("Decisiones de limpieza documentadas:")
bullet("Revolico '000' -> tratado como precio ausente (NaN), no como cero.")
bullet("Precios < 20 USD -> marcados flag_precio_bajo y excluidos de estadisticos (patron compatible con error de separador decimal: '1,150 USD' -> 1,15). No se corrige el valor: se excluye.")
bullet("Potencia > 2 000 W en categoria 'panel solar' -> flag_potencia_imposible y excluida de calculos por watt (panel comercial no supera ~700 W).")
bullet("Moneda != USD -> marcada y excluida.")
bullet("Municipios -> normalizados al catalogo oficial de los 15 municipios de La Habana (municipios.py). Lo que no coincide queda NaN; no se asigna por defecto.")
bullet("Marcas -> 20 grafias observadas (MUST/Must/must/MUSt, LONGi/Longi/LONGI...) unificadas a 11 marcas canonicas.")

sec("4. Procesamiento y estandarizacion")
para("Pipeline reproducible en 3 scripts, ejecutables desde la raiz de proyecto/:")
bullet("01_carga_limpieza.py: lee data/ y escribe outputs/tablas/*_limpio.csv (anuncios_limpio.csv, entrevistas_limpio.csv).")
bullet("02_analisis.py: escribe 15 tablas de analisis (kpi.csv, oferta_mensual.csv, precios_categoria.csv, brecha_oferta_compra.csv, marcas.csv, canales.csv, garantia.csv, economia_unitaria.csv, opacidad.csv, onei_balance.csv, onei_variacion.csv, calidad.csv, unit_valores.csv, categoria_anio.csv, baterias_detalle.csv).")
bullet("03_graficos.py: escribe 12 PNG en outputs/figuras/ (01_onei_contexto.png ... 12_equipamiento.png).")
para("El cuaderno notebooks/storytelling.ipynb ejecuta el pipeline por si mismo en la celda de la seccion 4, por lo que funciona con Run All sin haber corrido los scripts antes.")
para("Transformaciones clave: calculo de precio por vatio (precio_w_usd = precio / potencia_w), disponibilidad por campo (% no-nulos), normalizacion de marcas y municipios, flags de calidad, cruce oferta vs compra.")

sec("5. Hallazgos principales")
bullet("Electricidad disponible Cuba 2019->2022 (ONEI): -13,4 % (21 155 -> 18 323 GWh).")
bullet("Importacion generacion movil 2019->2022 (ONEI): +476 % (449 -> 2 591 GWh).")
bullet("Anuncios publicados: 352 en 2 canales, 2022-06 a 2026-10 (Telegram); 30 Revolico sin fecha.")
bullet("Anuncios de panel solar sin precio: 58,0 % (112 de 193). Anuncios de kit solar sin precio: 9,5 % (4 de 42).")
bullet("Precio mediano anunciado (panel, USD/W): 0,364 (n=71). Precio mediano pagado (panel, USD/W): 0,267 (n=35). Brecha oferta vs compra: -27 %.")
bullet("Anuncios que mencionan garantia: 11,9 % (42 de 352). Compras con garantia obtenida: 51,4 % (18 de 35); 12 de ellas de 1 mes.")
bullet("Marca lider en la oferta: MUST, 62 de 98 anuncios con marca (63 %). Presencia de MUST en las compras: 0 de 35.")
bullet("Compras que incluyen bateria: 31 de 35 (89 %). Compras que incluyen inversor: 15 de 35 (43 %).")
bullet("94,9 % de los anuncios de Telegram sin municipio: no se realizo analisis territorial.")

sec("6. Limitaciones")
bullet("n=35 en la demanda: comparaciones descriptivas, no inferenciales.")
bullet("Sin fecha de compra en entrevistas.json y sin fecha en Revolico: no hay serie temporal de la demanda.")
bullet("94,9 % de los anuncios de Telegram sin municipio: no se hizo analisis territorial.")
bullet("Los precios son declaraciones, no facturas verificadas.")
bullet("La serie de ONEI termina en 2022: es contexto, no causa.")
bullet("9 anuncios en EUR/CUP excluidos por falta de serie oficial de tipos de cambio (BCC).")
bullet("Revolucion de entrevistas (2026-11-06): el archivo entrevistas.json fue sustituido por una version revisada (61 valores modificados en 21 registros, campos nuevos dispone_de_bateria/dispone_de_inversor, garantias 13->18, mediana pagada 0,309->0,267, brecha -15,0 % -> -26,6 %). Los graficos 08, 09, 10, 11 y 12 se recalcularon.")

sec("7. Conclusiones")
para("Se construyo un pipeline reproducible (carga->limpieza->analisis->graficos) y un embudo crudo->analizable que hace visible la opacidad del mercado solar habanero. Los hallazgos clave: la mayoria de los anuncios de panel omite el precio (58 %), la brecha oferta-compra es del -27 %, la marca lider en anuncios (MUST) no aparece en ninguna compra, y la garantia es mas promesa que contrato (12 de 1 mes). La evidencia es limitada (n=35, sin fecha, sin municipio) pero rigurosa: nada se imputo ni se invento, los errores se marcaron y los datos faltantes quedaron como NaN.")

pdf.output("C:/Users/Ramsés/Documents/proyecto anthony (2)/proyecto anthony/proyecto cd/proyecto/informe_tecnico.pdf")
print("OK")