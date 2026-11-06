# -*- coding: utf-8 -*-
"""
01_carga_limpieza.py
====================
Carga, valida y limpia las tres fuentes de datos del proyecto y deja
tablas intermedias en ``outputs/tablas/``.

Reglas del proyecto que este script respeta:
  * No se inventa ni se imputa ningún valor. Lo que falta queda como NaN
    y se documenta con una bandera ``flag_*``.
  * Los precios en EUR/CUP NO se convierten: no se descargó una serie
    oficial de tipos de cambio, y convertir con una tasa inventada sería
    fabricar datos. Se marcan como ``moneda_no_usd`` y se excluyen de los
    análisis de precio.
  * Los precios "000" de Revolico se tratan como dato ausente (el propio
    informe del proyecto los documenta como "precio no capturado").

Ejecución:  python scripts/01_carga_limpieza.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Rutas (siempre relativas a la raíz del proyecto)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
DIR_RAW = RAIZ / "data" / "raw"
DIR_FUENTES = RAIZ / "data" / "fuentes"
DIR_TABLAS = RAIZ / "outputs" / "tablas"
DIR_TABLAS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------


def _sin_acentos(texto: str) -> str:
    """Devuelve el texto en minúsculas y sin tildes."""
    if not isinstance(texto, str):
        return ""
    normal = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normal if not unicodedata.combining(c)).lower().strip()


def leer_json(ruta: Path):
    """Carga un JSON con mensajes de error explícitos."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo requerido: {ruta}")
    try:
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON corrupto en {ruta.name}: {exc}") from exc


def validar_columnas(df: pd.DataFrame, requeridas: list[str], nombre: str) -> None:
    """Falla rápido si falta una columna imprescindible."""
    faltan = [c for c in requeridas if c not in df.columns]
    if faltan:
        raise KeyError(f"{nombre}: faltan columnas {faltan}. Presentes: {list(df.columns)}")


# ---------------------------------------------------------------------------
# Municipios: catálogo canónico de La Habana (15 municipios)
# Fuente: división político-administrativa vigente, ya codificada en el
# proyecto original (municipios.py). No se inventa ningún municipio: si el
# texto no coincide, se devuelve NaN.
# ---------------------------------------------------------------------------
_MUNICIPIOS = {
    "arroyo naranjo": "Arroyo Naranjo",
    "boyeros": "Boyeros",
    "centro habana": "Centro Habana",
    "cerro": "Cerro",
    "cotorro": "Cotorro",
    "diez de octubre": "Diez de Octubre",
    "10 de octubre": "Diez de Octubre",
    "guanabacoa": "Guanabacoa",
    "habana del este": "Habana del Este",
    "la habana del este": "Habana del Este",
    "la lisa": "La Lisa",
    "marianao": "Marianao",
    "playa": "Playa",
    "plaza": "Plaza de la Revolución",
    "plaza de la revolucion": "Plaza de la Revolución",
    "regla": "Regla",
    "san miguel del padron": "San Miguel del Padrón",
    "habana vieja": "Habana Vieja",
}


def municipio_canonico(valor) -> str | None:
    """Normaliza variantes de escritura ('Plaza', 'centro habana'...) al nombre oficial."""
    return _MUNICIPIOS.get(_sin_acentos(valor))


# ---------------------------------------------------------------------------
# Marcas: se agrupan las grafías observadas en el propio dataset
# (MUST/Must/must/MUSt -> MUST, LONGi/Longi/LONGI -> Longi, etc.).
# ---------------------------------------------------------------------------
_MARCAS = {
    "must": "MUST", "must solar": "MUST",
    "longi": "Longi", "longi solar": "Longi",
    "jinko": "JinkoSolar", "jinkosolar": "JinkoSolar", "jinko solar": "JinkoSolar",
    "ja solar": "JA Solar", "jasolar": "JA Solar",
    "trina solar": "Trina Solar", "trinasolar": "Trina Solar", "trina": "Trina Solar",
    "canadian solar": "Canadian Solar", "canadian": "Canadian Solar",
    "seraphim": "Seraphim",
    "bluesun": "Bluesun",
    "boviet solar": "Boviet Solar", "boviet": "Boviet Solar",
    "ronma": "RONMA",
    "suncar": "Suncar",
}


def normalizar_marca(valor) -> str | None:
    """Devuelve la marca canónica o el texto original si no está en el catálogo."""
    if not isinstance(valor, str) or not valor.strip():
        return None
    clave = _sin_acentos(valor).replace("  ", " ")
    if clave in _MARCAS:
        return _MARCAS[clave]
    # variantes con prefijo (p. ej. "MUST PV18")
    for variante, canonica in _MARCAS.items():
        if clave.startswith(variante + " "):
            return canonica
    return valor.strip().title()


# ---------------------------------------------------------------------------
# 1. Anuncios de Telegram (352 registros, con fecha)
# ---------------------------------------------------------------------------
def cargar_anuncios_telegram() -> pd.DataFrame:
    datos = leer_json(DIR_RAW / "telegram_anuncios.json")
    if not isinstance(datos, list) or not datos:
        raise ValueError("telegram_anuncios.json debe ser una lista no vacía")

    df = pd.DataFrame(datos)
    validar_columnas(
        df,
        ["id", "fecha_publicacion", "categoria_producto", "potencia_w", "precio", "moneda", "url"],
        "telegram",
    )

    df["fuente"] = "Telegram"
    df["canal"] = df["canal"].astype(str)
    df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)
    df["categoria"] = df["categoria_producto"].astype(str).str.strip().str.lower()

    for col in ("potencia_w", "precio", "energia_kwh", "capacidad_ah",
                "voltaje_nominal_v", "potencia_inversor_w"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["moneda"] = df["moneda"].astype("string").str.upper()
    return df


# ---------------------------------------------------------------------------
# 2. Anuncios de Revolico (30 registros, SIN fecha de publicación)
# ---------------------------------------------------------------------------
def cargar_anuncios_revolico() -> pd.DataFrame:
    datos = leer_json(DIR_RAW / "revolico_anuncios.json")
    if not isinstance(datos, list) or not datos:
        raise ValueError("revolico_anuncios.json debe ser una lista no vacía")

    df = pd.DataFrame(datos)
    validar_columnas(df, ["url", "precio", "potencia", "municipio"], "revolico")

    df["fuente"] = "Revolico"
    df["id"] = [f"rev-{i:03d}" for i in range(len(df))]
    df["canal"] = "Revolico"

    # precio llega como texto ("385", "000"); "000" = precio no capturado
    precio_num = pd.to_numeric(df["precio"], errors="coerce")
    df["precio_cero"] = precio_num.eq(0)
    df["precio"] = precio_num.mask(precio_num.eq(0))

    # potencia llega como "620W" o "4000W"
    df["potencia_w"] = pd.to_numeric(
        df["potencia"].astype("string").str.extract(r"(\d+(?:\.\d+)?)")[0],
        errors="coerce",
    )

    df["moneda"] = df["moneda"].astype("string").str.upper()
    df["categoria"] = pd.NA
    df["fecha_publicacion"] = pd.NaT  # Revolico no expone fecha de publicación

    # Heurística declarada (no es un dato del anuncio): el título decide si es
    # panel suelto o kit. Se documenta como variable derivada.
    titulo = df["titulo"].astype("string").str.lower()
    df["categoria"] = pd.NA
    df.loc[titulo.str.contains("kit|combo|sistema", na=False), "categoria"] = "kit solar"
    df.loc[titulo.str.contains("bater", na=False), "categoria"] = "batería"
    df.loc[titulo.str.contains("inversor", na=False), "categoria"] = "inversor"
    df.loc[titulo.str.contains("panel|paneles|placa", na=False) & df["categoria"].isna(), "categoria"] = "panel solar"
    df["categoria"] = df["categoria"].fillna("no determinado")

    df["municipio_original"] = df["municipio"]
    df["municipio"] = df["municipio"].map(municipio_canonico)
    df["garantia"] = df.get("garantia")
    return df


# ---------------------------------------------------------------------------
# 3. Entrevistas (35 compras reales, SIN fecha de compra)
# ---------------------------------------------------------------------------
_RENOMBRES_ENTREVISTAS = {
    "modelo": "tipo_de_panel",  # el esquema nuevo renombró "modelo" a "tipo_de_panel"
    "potencia_por_anel": "potencia_por_panel",
    "potencia_por_panel_w": "potencia_por_panel",
    "potencia_total_w": "potencia_total",
    "potencia total": "potencia_total",
    "cantidad de paneles": "cantidad_de_paneles",
    "lugar de adquisicion": "lugar_de_adquisicion",
    "vida util": "vida_util",
}


def colapsar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Une columnas con el mismo nombre (la primera aparición gana; luego se completa con las demás)."""
    if not df.columns.duplicated().any():
        return df
    salida = pd.DataFrame(index=df.index)
    for nombre in dict.fromkeys(df.columns):
        bloque = df.loc[:, df.columns == nombre]
        serie = bloque.iloc[:, 0]
        for k in range(1, bloque.shape[1]):
            serie = serie.combine_first(bloque.iloc[:, k])
        salida[nombre] = serie
    return salida


def cargar_entrevistas() -> pd.DataFrame:
    datos = leer_json(DIR_RAW / "entrevistas.json")
    if not isinstance(datos, dict) or "paneles" not in datos:
        raise ValueError("entrevistas.json debe ser un objeto con la clave 'paneles'")

    df = pd.DataFrame(datos["paneles"])
    df = df.rename(columns={k: v for k, v in _RENOMBRES_ENTREVISTAS.items() if k in df.columns})
    df = colapsar_columnas(df)
    validar_columnas(
        df,
        ["id", "municipio", "precio_por_panel", "lugar_de_adquisicion"],
        "entrevistas",
    )

    for col in ("precio_por_panel", "potencia_por_panel", "potencia_total"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["cantidad_de_paneles"] = pd.to_numeric(df["cantidad_de_paneles"], errors="coerce")
    df["garantia"] = pd.to_numeric(df["garantia"], errors="coerce")
    df["vida_util"] = pd.to_numeric(df["vida_util"], errors="coerce")

    # Campos binarios incorporados en la revisión de 2026-11-06.
    # Si el archivo no los trae (versión anterior), quedan como <NA> y no se usan.
    for col in ("dispone_de_bateria", "dispone_de_inversor"):
        if col in df.columns:
            df[col] = df[col].map({True: True, False: False, "True": True, "False": False})
            df[col] = df[col].astype("boolean")
        else:
            df[col] = pd.NA
            df[col] = df[col].astype("boolean")

    df["municipio_original"] = df["municipio"]
    df["municipio"] = df["municipio"].map(municipio_canonico)
    df["marca"] = df["marca"].map(normalizar_marca)
    df["lugar_de_adquisicion"] = (
        df["lugar_de_adquisicion"].astype("string").str.strip().str.title()
    )
    df["fuente"] = "Entrevistas"
    df["fecha_compra"] = pd.NaT  # el instrumento no registró fecha

    # Métricas derivadas (aritmética sobre datos medidos, no estimaciones)
    df["usd_por_w"] = df["precio_por_panel"] / df["potencia_por_panel"]
    df["kw_instalados"] = df["potencia_total"] / 1000.0
    df["gasto_usd"] = df["precio_por_panel"] * df["cantidad_de_paneles"]
    return df


# ---------------------------------------------------------------------------
# 4. ONEI: Balance de electricidad 2019-2022 (XLSX oficial)
# ---------------------------------------------------------------------------
_INDICADORES = {
    "fuentes": "Fuentes (suministro total)",
    "importacion de energia electrica": "Importación (generación móvil)",
    "consumo": "Consumo total",
    "residencial": "Consumo residencial",
    "perdidas": "Pérdidas",
}


def cargar_balance_onei() -> pd.DataFrame:
    """Convierte el XLSX de ONEI (tres bloques de dos años) en formato largo."""
    import openpyxl

    ruta = DIR_FUENTES / "onei_10.14_balance_electricidad.xlsx"
    if not ruta.exists():
        raise FileNotFoundError(f"Falta la descarga oficial: {ruta}")

    hoja = openpyxl.load_workbook(ruta, data_only=True)["10.14"]
    filas = list(hoja.iter_rows(values_only=True))

    # Fila 6 contiene las cabeceras DESCRIPCION | año | año
    cabecera = filas[5]
    bloques = []
    for col, valor in enumerate(cabecera):
        if isinstance(valor, str) and _sin_acentos(valor) == "descripcion":
            anios = []
            for k in (1, 2):
                try:
                    anios.append(int(cabecera[col + k]))
                except (TypeError, ValueError):
                    continue
            if len(anios) == 2:
                bloques.append((col, anios))
    if len(bloques) != 3:
        raise ValueError(f"Se esperaban 3 bloques de años en el balance; hay {len(bloques)}")

    registros = []
    for col, anios in bloques:
        for fila in filas[6:]:
            etiqueta = _sin_acentos(fila[col]) if col < len(fila) else ""
            if etiqueta not in _INDICADORES:
                continue
            for k, anio in enumerate(anios, start=1):
                valor = fila[col + k] if col + k < len(fila) else None
                if isinstance(valor, (int, float)):
                    registros.append(
                        {"indicador": _INDICADORES[etiqueta], "anio": anio, "valor_gwh": float(valor)}
                    )

    df = pd.DataFrame(registros).drop_duplicates(subset=["indicador", "anio"], keep="last")
    df["fuente"] = "ONEI, Anuario Estadístico de Cuba, tabla 10.14"
    if df.empty:
        raise ValueError("El balance de ONEI no produjo registros")
    return df.sort_values(["indicador", "anio"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 5. Construcción de la tabla unificada de anuncios
# ---------------------------------------------------------------------------
def construir_anuncios() -> pd.DataFrame:
    telegram = cargar_anuncios_telegram()
    revolico = cargar_anuncios_revolico()

    columnas = [
        "id", "fuente", "canal", "fecha_publicacion", "categoria", "marca", "modelo",
        "potencia_w", "precio", "moneda", "estado", "garantia", "vida_util",
        "tipo_panel", "municipio", "municipio_original", "provincia", "url",
        "potencia_inversor_w", "capacidad_ah", "voltaje_nominal_v", "energia_kwh",
        "tipo_bateria",
    ]
    for col in columnas:
        if col not in telegram.columns:
            telegram[col] = pd.NA
        if col not in revolico.columns:
            revolico[col] = pd.NA

    # Revolico no trae varias columnas: se crean vacías para poder concatenar.
    # (El aviso de pandas sobre columnas totalmente vacías es esperado aquí.)
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        anuncios = pd.concat([telegram[columnas], revolico[columnas]], ignore_index=True)
    anuncios["fecha_publicacion"] = pd.to_datetime(
        anuncios["fecha_publicacion"], errors="coerce", utc=True
    )

    anuncios["marca_original"] = anuncios["marca"]
    anuncios["marca"] = anuncios["marca"].map(normalizar_marca)
    anuncios["municipio_original"] = anuncios["municipio_original"].fillna(anuncios["municipio"])
    anuncios["municipio"] = anuncios["municipio"].map(municipio_canonico)
    anuncios["anio"] = anuncios["fecha_publicacion"].dt.year
    anuncios["mes"] = anuncios["fecha_publicacion"].dt.strftime("%Y-%m")
    anuncios["precio_usd"] = anuncios["precio"].where(anuncios["moneda"].eq("USD"))

    # Banderas de calidad (no eliminan filas: hacen visible el problema)
    anuncios["flag_sin_precio"] = anuncios["precio"].isna().fillna(False).astype(bool)
    anuncios["flag_moneda_no_usd"] = (
        anuncios["moneda"].notna() & anuncios["moneda"].ne("USD")
    ).fillna(False).astype(bool)
    anuncios["flag_precio_bajo"] = anuncios["precio_usd"].lt(20).fillna(False).astype(bool)
    anuncios["flag_potencia_imposible"] = (
        anuncios["categoria"].eq("panel solar") & anuncios["potencia_w"].gt(2000)
    ).fillna(False).astype(bool)
    anuncios["precio_w_usd"] = (
        anuncios["precio_usd"] / anuncios["potencia_w"]
    ).where(
        anuncios["categoria"].eq("panel solar")
        & anuncios["potencia_w"].between(100, 2000)
        & anuncios["precio_usd"].ge(20)
    )

    return anuncios.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 6. Validaciones e informes
# ---------------------------------------------------------------------------
def validar_anuncios(df: pd.DataFrame) -> None:
    assert df["id"].notna().all(), "Hay anuncios sin id"
    assert df["url"].notna().all(), "Hay anuncios sin URL"
    assert df["url"].is_unique, "Hay URLs duplicadas"
    categorias_validas = {"panel solar", "batería", "kit solar", "inversor", "no determinado"}
    assert set(df["categoria"].dropna().unique()) <= categorias_validas, "Categoría inesperada"
    con_fecha = df.dropna(subset=["fecha_publicacion"])
    assert len(con_fecha) == df["fuente"].eq("Telegram").sum(), "Fechas perdidas en Telegram"


def validar_entrevistas(df: pd.DataFrame) -> None:
    assert df["id"].is_unique, "IDs de entrevista duplicados"
    assert df["precio_por_panel"].notna().all(), "Falta el precio en alguna entrevista"
    # potencia_total debe ser exactamente potencia_por_panel * cantidad
    ambas = df.dropna(subset=["potencia_por_panel", "potencia_total", "cantidad_de_paneles"])
    calculado = ambas["potencia_por_panel"] * ambas["cantidad_de_paneles"]
    assert (calculado == ambas["potencia_total"]).all(), "potencia_total incoherente"


def main() -> None:
    anuncios = construir_anuncios()
    entrevistas = cargar_entrevistas()
    balance = cargar_balance_onei()

    validar_anuncios(anuncios)
    validar_entrevistas(entrevistas)

    anuncios.to_csv(DIR_TABLAS / "anuncios_limpio.csv", index=False, encoding="utf-8")
    entrevistas.to_csv(DIR_TABLAS / "entrevistas_limpio.csv", index=False, encoding="utf-8")
    balance.to_csv(DIR_TABLAS / "onei_balance.csv", index=False, encoding="utf-8")

    print(f"OK  anuncios   : {len(anuncios):>4} filas  ({anuncios['fuente'].value_counts().to_dict()})")
    print(f"OK  entrevistas: {len(entrevistas):>4} filas")
    print(f"OK  balance    : {len(balance):>4} filas  ({balance['indicador'].nunique()} indicadores)")
    print(f"    rango de fechas Telegram: {anuncios['fecha_publicacion'].min():%Y-%m-%d} -> "
          f"{anuncios['fecha_publicacion'].max():%Y-%m-%d}")
    print(f"    sin precio: {anuncios['flag_sin_precio'].sum()} "
          f"({100 * anuncios['flag_sin_precio'].mean():.1f} %)")


if __name__ == "__main__":
    main()
