import json
import re
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------
# LIMPIEZA DEL TEXTO
# ---------------------------------------------------------
def limpiar_texto(texto):
    basura = [
        "entra o regístrate", "publicar anuncio", "inicio >", "hogar >", "servicios >",
        "plantas y estaciones de energía >", "construcción y mantenimiento >", "la habana >",
        "centro habana >", "plaza >", "playa >", "1 / 10", "favorito", "compartir"
    ]
    t = texto.lower()
    for b in basura:
        t = t.replace(b, "")
    return t.strip()


# ---------------------------------------------------------
# IA LOCAL PARA EXTRAER TODOS LOS DATOS
# ---------------------------------------------------------
def extraer_datos(texto):

    # --- Precio ---
    precio_patron = r"(\d{2,6})\s*(usd|mlc|cup|\$)"
    m = re.search(precio_patron, texto)
    precio = m.group(1) if m else None
    moneda = m.group(2).upper() if m else None
    if moneda == "$":
        moneda = "USD"

    # --- Potencia ---
    potencia_patron = r"(\d{2,4})\s*(w|watts)"
    p = re.search(potencia_patron, texto)
    potencia = (p.group(1) + "W") if p else None

    # --- Marca ---
    marcas = ["longi", "boviet", "lvyuan", "ja solar", "trina", "canadian", "ampace", "andes", "parlet"]
    marca = None
    for m in marcas:
        if m in texto:
            marca = m.capitalize()
            break

    # --- Modelo (ELIMINADO) ---
    modelo = None

    # --- Ubicación ---
    municipios = [
        "plaza", "centro habana", "playa", "habana vieja", "guanabacoa",
        "san miguel", "cerro", "marianao", "boyeros", "arroyo naranjo"
    ]
    provincia = "La Habana"
    municipio = None
    for m in municipios:
        if m in texto:
            municipio = m.capitalize()
            break

    # --- Garantía ---
    garantia_patron = r"(garantía|meses de garantía|año de garantía|meses|año)"
    g = re.search(garantia_patron, texto)
    garantia = g.group(1) if g else None

    # --- Tipo de panel ---
    tipos = {
        "monocristalino": "Monocristalino",
        "policristalino": "Policristalino",
        "bifacial": "Bifacial",
        "portátil": "Portátil",
        "portable": "Portátil"
    }
    tipo_panel = None
    for palabra, tipo in tipos.items():
        if palabra in texto:
            tipo_panel = tipo
            break

    # --- Accesorios ---
    accesorios_claves = [
        "inversor", "batería", "cable", "conectores", "bases",
        "controlador", "regulador", "estructura", "kit", "breaker"
    ]
    accesorios = []
    for a in accesorios_claves:
        if a in texto:
            accesorios.append(a.capitalize())

    accesorios = accesorios if accesorios else None

    # --- Estado ---
    if "nuevo" in texto or "sellado" in texto:
        estado = "Nuevo"
    elif "usado" in texto or "uso" in texto:
        estado = "Usado"
    else:
        estado = None

    # --- Descripción (siempre null) ---
    descripcion = None

    return {
        "precio": precio,
        "moneda": moneda,
        "potencia": potencia,
        "marca": marca,
        "modelo": modelo,
        "municipio": municipio,
        "provincia": provincia,
        "garantia": garantia,
        "tipo_panel": tipo_panel,
        "accesorios": accesorios,
        "estado": estado,
        "descripcion": descripcion
    }


# ---------------------------------------------------------
# SCRAPING DE CADA ANUNCIO
# ---------------------------------------------------------
def scrape_item(page, url):
    page.goto(url, timeout=60000)

    texto_completo = page.inner_text("*")
    texto_limpio = limpiar_texto(texto_completo)

    titulo = page.query_selector("h1").inner_text() if page.query_selector("h1") else None

    datos = extraer_datos(texto_limpio)
    datos["titulo"] = titulo
    datos["url"] = url

    return datos


# ---------------------------------------------------------
# SCRAPING DE LA BÚSQUEDA
# ---------------------------------------------------------
def scrape_revolico(query="paneles solares", limite=30):
    search_url = f"https://www.revolico.com/search?q={query.replace(' ', '+')}"
    resultados = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context()
        page = context.new_page()

        page.goto(search_url, timeout=60000)

        anuncios = page.query_selector_all('li[data-cy="adGrid"] a')

        urls = []
        for a in anuncios[:limite]:
            href = a.get_attribute("href")
            if href:
                urls.append("https://www.revolico.com" + href)

        for url in urls:
            datos = scrape_item(page, url)
            resultados.append(datos)

        browser.close()

    return resultados


# ---------------------------------------------------------
# GUARDAR JSON
# ---------------------------------------------------------
def guardar_json(datos, archivo="paneles_solares_completo.json"):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    datos = scrape_revolico("paneles solares", limite=30)
    guardar_json(datos)
    print("Scraping completado. Archivo generado: paneles_solares_completo.json")


if __name__ == "__main__":
    main()
