# -*- coding: utf-8 -*-
"""
02_analisis.py
==============
Calcula todas las tablas de análisis del proyecto a partir de las tablas
limpias de ``outputs/tablas/`` y las guarda como CSV.

No hay cifras escritas a mano: todo se deriva de los datos cargados.
Las reglas de filtrado están declaradas en constantes y se documentan en
cada tabla resultante.

Ejecución:  python scripts/02_analisis.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DIR_TABLAS = RAIZ / "outputs" / "tablas"

# --- Reglas de validez (declaradas, no ajustadas a los resultados) ----------
POTENCIA_PANEL = (100, 2000)        # W: rango físicamente posible de un panel
POTENCIA_INVERSOR = (500, 100_000)  # W
ENERGIA_BATERIA = (0.5, 100)        # kWh
PRECIO_MINIMO = 20                  # USD: por debajo, el precio es un error de parseo
CATEGORIAS = ["panel solar", "batería", "kit solar", "inversor"]


def cargar(nombre: str) -> pd.DataFrame:
    ruta = DIR_TABLAS / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta}. Ejecuta antes scripts/01_carga_limpieza.py")
    df = pd.read_csv(ruta)
    if "fecha_publicacion" in df.columns:
        df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce", utc=True)
        df["anio"] = df["fecha_publicacion"].dt.year
    for col in ("anio", "potencia_w", "precio", "precio_usd", "precio_w_usd",
                "potencia_inversor_w", "capacidad_ah", "voltaje_nominal_v"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("flag_sin_precio", "flag_precio_bajo", "flag_potencia_imposible", "flag_moneda_no_usd"):
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    return df


def _resumen(serie: pd.Series) -> dict:
    serie = serie.dropna()
    if serie.empty:
        return {"n": 0}
    return {
        "n": int(serie.size),
        "p25": round(float(serie.quantile(0.25)), 2),
        "mediana": round(float(serie.median()), 2),
        "p75": round(float(serie.quantile(0.75)), 2),
        "min": round(float(serie.min()), 2),
        "max": round(float(serie.max()), 2),
    }


# ---------------------------------------------------------------------------
# 1. Indicadores generales
# ---------------------------------------------------------------------------
def tabla_kpi(anuncios: pd.DataFrame, entrevistas: pd.DataFrame, balance: pd.DataFrame) -> pd.DataFrame:
    telegram = anuncios[anuncios["fuente"] == "Telegram"]
    filas = [
        ("anuncios_totales", len(anuncios)),
        ("anuncios_telegram", len(telegram)),
        ("anuncios_revolico", int((anuncios["fuente"] == "Revolico").sum())),
        ("entrevistas_totales", len(entrevistas)),
        ("fecha_min", f"{telegram['fecha_publicacion'].min():%Y-%m-%d}"),
        ("fecha_max", f"{telegram['fecha_publicacion'].max():%Y-%m-%d}"),
        ("anuncios_sin_precio", int(telegram["flag_sin_precio"].sum())),
        ("pct_sin_precio", round(100 * telegram["flag_sin_precio"].mean(), 1)),
        ("anuncios_con_marca", int(telegram["marca"].notna().sum())),
        ("pct_con_marca", round(100 * telegram["marca"].notna().mean(), 1)),
        ("municipios_oferta", int(telegram["municipio"].nunique())),
        ("municipios_demanda", int(entrevistas["municipio"].nunique())),
        ("onei_indicadores", int(balance["indicador"].nunique())),
        ("onei_anio_min", int(balance["anio"].min())),
        ("onei_anio_max", int(balance["anio"].max())),
    ]
    return pd.DataFrame(filas, columns=["metrica", "valor"])


# ---------------------------------------------------------------------------
# 2. Serie temporal de la oferta (solo Telegram: Revolico no tiene fecha)
# ---------------------------------------------------------------------------
def tabla_oferta_mensual(anuncios: pd.DataFrame) -> pd.DataFrame:
    """Anuncios por mes. Se completa la rejilla temporal con 0 en los meses sin
    anuncios (ausencia de anuncio, no ausencia de dato): así la serie no tiene
    huecos artificiales."""
    telegram = anuncios[anuncios["fuente"] == "Telegram"].dropna(subset=["mes"])
    tabla = telegram.groupby("mes").size().rename("anuncios")
    rejilla = pd.period_range(tabla.index.min(), tabla.index.max(), freq="M").astype(str)
    tabla = tabla.reindex(rejilla, fill_value=0).rename_axis("mes").reset_index()
    tabla["media_movil_3m"] = tabla["anuncios"].rolling(3, min_periods=1).mean().round(1)
    return tabla


# ---------------------------------------------------------------------------
# 3. Composición por año y categoría
# ---------------------------------------------------------------------------
def tabla_categoria_anio(anuncios: pd.DataFrame) -> pd.DataFrame:
    telegram = anuncios[(anuncios["fuente"] == "Telegram") & anuncios["anio"].notna()]
    tabla = (
        telegram.groupby(["anio", "categoria"]).size().rename("n").reset_index()
    )
    tabla["anio"] = tabla["anio"].astype(int)
    totales = tabla.groupby("anio")["n"].transform("sum")
    tabla["pct"] = (100 * tabla["n"] / totales).round(1)
    return tabla.sort_values(["anio", "n"], ascending=[True, False])


# ---------------------------------------------------------------------------
# 4. Opacidad: anuncios sin precio
# ---------------------------------------------------------------------------
def tabla_opacidad(anuncios: pd.DataFrame) -> pd.DataFrame:
    telegram = anuncios[anuncios["fuente"] == "Telegram"]
    tabla = (
        telegram.groupby("categoria")
        .agg(n=("id", "size"), sin_precio=("flag_sin_precio", "sum"))
        .reset_index()
    )
    tabla["pct_sin_precio"] = (100 * tabla["sin_precio"] / tabla["n"]).round(1)
    return tabla.sort_values("pct_sin_precio", ascending=False)


# ---------------------------------------------------------------------------
# 5. Precios anunciados por categoría (solo USD, precio plausible)
# ---------------------------------------------------------------------------
def tabla_precios(anuncios: pd.DataFrame) -> pd.DataFrame:
    base = anuncios[
        anuncios["precio_usd"].notna() & anuncios["precio_usd"].ge(PRECIO_MINIMO)
    ]
    filas = []
    for cat in CATEGORIAS:
        sub = base[base["categoria"] == cat]["precio_usd"]
        fila = {"categoria": cat, **_resumen(sub)}
        filas.append(fila)
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 6. Economía unitaria: USD/W y USD/kWh
# ---------------------------------------------------------------------------
def tabla_economia_unitaria(anuncios: pd.DataFrame) -> pd.DataFrame:
    usd = anuncios[anuncios["moneda"].eq("USD") & anuncios["precio"].ge(PRECIO_MINIMO)]
    filas = []

    paneles = usd[
        usd["categoria"].eq("panel solar")
        & usd["potencia_w"].between(*POTENCIA_PANEL)
    ]
    filas.append({"metrica": "Panel solar (USD/W)", "categoria": "panel solar",
                  **_resumen(paneles["precio"] / paneles["potencia_w"])})

    inversores = usd[
        usd["categoria"].eq("inversor")
        & usd["potencia_inversor_w"].between(*POTENCIA_INVERSOR)
    ]
    filas.append({"metrica": "Inversor (USD/W)", "categoria": "inversor",
                  **_resumen(inversores["precio"] / inversores["potencia_inversor_w"])})

    kits = usd[usd["categoria"].eq("kit solar") & usd["potencia_w"].between(*POTENCIA_PANEL)]
    filas.append({"metrica": "Kit solar (USD/W)", "categoria": "kit solar",
                  **_resumen(kits["precio"] / kits["potencia_w"])})

    baterias = usd[usd["categoria"].eq("batería")].copy()
    baterias["kwh"] = baterias["capacidad_ah"] * baterias["voltaje_nominal_v"] / 1000.0
    baterias = baterias[baterias["kwh"].between(*ENERGIA_BATERIA)]
    filas.append({"metrica": "Batería (USD/kWh)", "categoria": "batería",
                  **_resumen(baterias["precio"] / baterias["kwh"])})

    return pd.DataFrame(filas)


def tabla_unit_valores(anuncios: pd.DataFrame) -> pd.DataFrame:
    """Valores unitarios individuales (para boxplots y dispersión)."""
    usd = anuncios[anuncios["moneda"].eq("USD") & anuncios["precio"].ge(PRECIO_MINIMO)]
    piezas = []

    pan = usd[usd["categoria"].eq("panel solar") & usd["potencia_w"].between(*POTENCIA_PANEL)]
    piezas.append(pd.DataFrame({
        "categoria": "panel solar", "metrica": "usd_w",
        "valor": pan["precio"] / pan["potencia_w"], "id": pan["id"],
    }))

    inv = usd[usd["categoria"].eq("inversor") & usd["potencia_inversor_w"].between(*POTENCIA_INVERSOR)]
    piezas.append(pd.DataFrame({
        "categoria": "inversor", "metrica": "usd_w",
        "valor": inv["precio"] / inv["potencia_inversor_w"], "id": inv["id"],
    }))

    kit = usd[usd["categoria"].eq("kit solar") & usd["potencia_w"].between(*POTENCIA_PANEL)]
    piezas.append(pd.DataFrame({
        "categoria": "kit solar", "metrica": "usd_w",
        "valor": kit["precio"] / kit["potencia_w"], "id": kit["id"],
    }))

    bat = usd[usd["categoria"].eq("batería")].copy()
    bat["kwh"] = bat["capacidad_ah"] * bat["voltaje_nominal_v"] / 1000.0
    bat = bat[bat["kwh"].between(*ENERGIA_BATERIA)]
    piezas.append(pd.DataFrame({
        "categoria": "batería", "metrica": "usd_kwh",
        "valor": bat["precio"] / bat["kwh"], "id": bat["id"],
    }))

    return pd.concat(piezas, ignore_index=True).dropna(subset=["valor"])


def tabla_baterias_detalle(anuncios: pd.DataFrame) -> pd.DataFrame:
    """Detalle de baterías usadas en el cálculo de USD/kWh (trazabilidad)."""
    usd = anuncios[anuncios["moneda"].eq("USD") & anuncios["precio"].ge(PRECIO_MINIMO)]
    bat = usd[usd["categoria"].eq("batería")].copy()
    bat["kwh"] = bat["capacidad_ah"] * bat["voltaje_nominal_v"] / 1000.0
    bat = bat[bat["kwh"].between(*ENERGIA_BATERIA)]
    bat["usd_kwh"] = bat["precio"] / bat["kwh"]
    return bat[["id", "canal", "precio", "capacidad_ah", "voltaje_nominal_v",
                "kwh", "usd_kwh", "tipo_bateria"]].sort_values("usd_kwh")


# ---------------------------------------------------------------------------
# 7. Brecha oferta vs compra (USD/W)
# ---------------------------------------------------------------------------
def tabla_sesgo_precio(anuncios: pd.DataFrame) -> pd.DataFrame:
    """Cuántos paneles publican precio: mide el sesgo de la comparación oferta-compra."""
    telegram = anuncios[anuncios["fuente"] == "Telegram"]
    paneles = telegram[telegram["categoria"] == "panel solar"]
    con_precio = int((paneles["moneda"] == "USD").sum())
    filas = [
        {"concepto": "Paneles anunciados", "n": len(paneles)},
        {"concepto": "Paneles con precio en USD", "n": con_precio},
    ]
    tabla = pd.DataFrame(filas)
    tabla["pct"] = (100 * tabla["n"] / len(paneles)).round(1)
    return tabla


def tabla_brecha(anuncios: pd.DataFrame, entrevistas: pd.DataFrame) -> pd.DataFrame:
    oferta = anuncios.loc[anuncios["precio_w_usd"].notna(), "precio_w_usd"]
    demanda = entrevistas["usd_por_w"].dropna()
    mediana_oferta = float(oferta.median())
    mediana_demanda = float(demanda.median())
    tabla = pd.DataFrame(
        [
            {"grupo": "Oferta anunciada", "n": int(oferta.size), "usd_w": round(mediana_oferta, 3)},
            {"grupo": "Compra declarada", "n": int(demanda.size), "usd_w": round(mediana_demanda, 3)},
        ]
    )
    tabla["brecha_pct"] = round(
        100 * (tabla["usd_w"] / mediana_oferta - 1), 1
    )
    return tabla


# ---------------------------------------------------------------------------
# 8. Canal de compra
# ---------------------------------------------------------------------------
def tabla_canales(entrevistas: pd.DataFrame) -> pd.DataFrame:
    df = entrevistas.dropna(subset=["lugar_de_adquisicion"]).copy()
    tabla = (
        df.groupby("lugar_de_adquisicion")
        .agg(
            n=("id", "size"),
            usd_w=("usd_por_w", "median"),
            precio_panel=("precio_por_panel", "median"),
            con_garantia=("garantia", lambda s: int(s.notna().sum())),
            cantidad=("cantidad_de_paneles", "median"),
        )
        .reset_index()
        .rename(columns={"lugar_de_adquisicion": "canal"})
    )
    tabla["pct_garantia"] = (100 * tabla["con_garantia"] / tabla["n"]).round(1)
    tabla["usd_w"] = tabla["usd_w"].round(3)
    return tabla.sort_values("n", ascending=False)


# ---------------------------------------------------------------------------
# 9. Garantía: oferta vs compra
# ---------------------------------------------------------------------------
def tabla_garantia(anuncios: pd.DataFrame, entrevistas: pd.DataFrame) -> pd.DataFrame:
    telegram = anuncios[anuncios["fuente"] == "Telegram"]
    filas = [
        {
            "grupo": "Oferta (anuncios)",
            "n": len(telegram),
            "con_garantia": int(telegram["garantia"].notna().sum()),
        },
        {
            "grupo": "Compra (entrevistas)",
            "n": len(entrevistas),
            "con_garantia": int(entrevistas["garantia"].notna().sum()),
        },
    ]
    tabla = pd.DataFrame(filas)
    tabla["pct"] = (100 * tabla["con_garantia"] / tabla["n"]).round(1)
    return tabla


def tabla_garantia_duracion(entrevistas: pd.DataFrame) -> pd.DataFrame:
    tabla = (
        entrevistas["garantia"].dropna().astype(int).value_counts()
        .rename_axis("meses").reset_index(name="n").sort_values("meses")
    )
    return tabla


# ---------------------------------------------------------------------------
# 10. Marcas: oferta vs demanda
# ---------------------------------------------------------------------------
def tabla_marcas(anuncios: pd.DataFrame, entrevistas: pd.DataFrame) -> pd.DataFrame:
    telegram = anuncios[anuncios["fuente"] == "Telegram"]
    oferta = telegram["marca"].dropna().value_counts()
    demanda = entrevistas["marca"].dropna().value_counts()
    marcas = sorted(set(oferta.index) | set(demanda.index))
    tabla = pd.DataFrame(
        {
            "marca": marcas,
            "oferta_n": [int(oferta.get(m, 0)) for m in marcas],
            "demanda_n": [int(demanda.get(m, 0)) for m in marcas],
        }
    )
    return tabla.sort_values("oferta_n", ascending=False)


# ---------------------------------------------------------------------------
# 11. ONEI: variación del suministro eléctrico
# ---------------------------------------------------------------------------
def tabla_onei(balance: pd.DataFrame) -> pd.DataFrame:
    pivot = balance.pivot_table(index="anio", columns="indicador", values="valor_gwh")
    filas = []
    for col in pivot.columns:
        serie = pivot[col].dropna()
        if len(serie) < 2:
            continue
        primero, ultimo = float(serie.iloc[0]), float(serie.iloc[-1])
        filas.append(
            {
                "indicador": col,
                "anio_inicial": int(serie.index[0]),
                "anio_final": int(serie.index[-1]),
                "valor_inicial_gwh": round(primero, 1),
                "valor_final_gwh": round(ultimo, 1),
                "variacion_pct": round(100 * (ultimo / primero - 1), 1),
            }
        )
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# 12. Tabla de calidad de datos
# ---------------------------------------------------------------------------
def tabla_calidad(anuncios: pd.DataFrame, entrevistas: pd.DataFrame) -> pd.DataFrame:
    telegram = anuncios[anuncios["fuente"] == "Telegram"]
    filas = [
        {"conjunto": "Telegram", "problema": "sin precio", "casos": int(telegram["flag_sin_precio"].sum()), "n": len(telegram)},
        {"conjunto": "Telegram", "problema": "precio < 20 USD", "casos": int(telegram["flag_precio_bajo"].sum()), "n": len(telegram)},
        {"conjunto": "Telegram", "problema": "potencia > 2000 W en panel", "casos": int(telegram["flag_potencia_imposible"].sum()), "n": len(telegram)},
        {"conjunto": "Telegram", "problema": "moneda distinta de USD", "casos": int(telegram["flag_moneda_no_usd"].sum()), "n": len(telegram)},
        {"conjunto": "Telegram", "problema": "sin marca", "casos": int(telegram["marca"].isna().sum()), "n": len(telegram)},
        {"conjunto": "Telegram", "problema": "sin municipio", "casos": int(telegram["municipio"].isna().sum()), "n": len(telegram)},
        {"conjunto": "Entrevistas", "problema": "sin garantía", "casos": int(entrevistas["garantia"].isna().sum()), "n": len(entrevistas)},
        {"conjunto": "Entrevistas", "problema": "sin vida útil", "casos": int(entrevistas["vida_util"].isna().sum()), "n": len(entrevistas)},
        {"conjunto": "Entrevistas", "problema": "sin fecha de compra", "casos": len(entrevistas), "n": len(entrevistas)},
    ]
    tabla = pd.DataFrame(filas)
    tabla["pct"] = (100 * tabla["casos"] / tabla["n"]).round(1)
    return tabla


def main() -> None:
    anuncios = cargar("anuncios_limpio.csv")
    entrevistas = cargar("entrevistas_limpio.csv")
    balance = cargar("onei_balance.csv")

    salidas = {
        "kpi.csv": tabla_kpi(anuncios, entrevistas, balance),
        "oferta_mensual.csv": tabla_oferta_mensual(anuncios),
        "categoria_anio.csv": tabla_categoria_anio(anuncios),
        "opacidad.csv": tabla_opacidad(anuncios),
        "precios_categoria.csv": tabla_precios(anuncios),
        "economia_unitaria.csv": tabla_economia_unitaria(anuncios),
        "unit_valores.csv": tabla_unit_valores(anuncios),
        "baterias_detalle.csv": tabla_baterias_detalle(anuncios),
        "brecha_oferta_compra.csv": tabla_brecha(anuncios, entrevistas),
        "sesgo_precio.csv": tabla_sesgo_precio(anuncios),
        "canales.csv": tabla_canales(entrevistas),
        "garantia.csv": tabla_garantia(anuncios, entrevistas),
        "garantia_duracion.csv": tabla_garantia_duracion(entrevistas),
        "marcas.csv": tabla_marcas(anuncios, entrevistas),
        "onei_variacion.csv": tabla_onei(balance),
        "calidad.csv": tabla_calidad(anuncios, entrevistas),
    }

    for nombre, df in salidas.items():
        assert not df.empty, f"La tabla {nombre} quedó vacía"
        df.to_csv(DIR_TABLAS / nombre, index=False, encoding="utf-8")
        print(f"OK  {nombre:<26} {len(df):>3} filas")

    print("\n--- Economía unitaria (medianas) ---")
    print(salidas["economia_unitaria.csv"][["metrica", "n", "mediana"]].to_string(index=False))
    print("\n--- Brecha oferta vs compra ---")
    print(salidas["brecha_oferta_compra.csv"].to_string(index=False))


if __name__ == "__main__":
    main()
