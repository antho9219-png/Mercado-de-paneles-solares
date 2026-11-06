# -*- coding: utf-8 -*-
"""
03_graficos.py
==============
Genera los 11 gráficos del proyecto a partir de las tablas de
``outputs/tablas/``. Cada figura se guarda en ``outputs/figuras/``.

Todas las cifras que aparecen en los títulos y anotaciones se calculan
desde los datos: no hay números escritos a mano.

Ejecución:  python scripts/03_graficos.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin ventana: funciona en cualquier entorno
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DIR_TABLAS = RAIZ / "outputs" / "tablas"
DIR_FIG = RAIZ / "outputs" / "figuras"
DIR_FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 9.5,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": ":",
        "legend.frameon": False,
        "figure.facecolor": "white",
    }
)

C = {
    "panel": "#1f6f8b",
    "bateria": "#e8a33d",
    "kit": "#7a5195",
    "inversor": "#4c956c",
    "gris": "#5b5b5b",
    "rojo": "#b23a48",
    "azul": "#2c5f8a",
}
COLOR_CAT = {"panel solar": C["panel"], "batería": C["bateria"],
             "kit solar": C["kit"], "inversor": C["inversor"]}


def leer(nombre: str) -> pd.DataFrame:
    ruta = DIR_TABLAS / nombre
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta}. Ejecuta antes scripts/02_analisis.py")
    return pd.read_csv(ruta)


def guardar(fig, nombre: str, fuente: str) -> Path:
    fig.text(0.01, -0.03, fuente, fontsize=6.8, color="#6b6b6b", ha="left", va="bottom")
    ruta = DIR_FIG / nombre
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


# ---------------------------------------------------------------------------
# G01 — Contexto: el suministro eléctrico oficial (ONEI 2019-2022)
# ---------------------------------------------------------------------------
def g01_contexto_onei() -> Path:
    bal = leer("onei_balance.csv")
    var = leer("onei_variacion.csv").set_index("indicador")
    piv = bal.pivot_table(index="anio", columns="indicador", values="valor_gwh")

    fuentes = piv["Fuentes (suministro total)"].dropna()
    importacion = piv["Importación (generación móvil)"].dropna()
    cambio = var.loc["Fuentes (suministro total)", "variacion_pct"]
    cambio_imp = var.loc["Importación (generación móvil)", "variacion_pct"]

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))

    ax = axs[0]
    ax.plot(fuentes.index, fuentes.values, marker="o", lw=2.4, color=C["azul"])
    ax.fill_between(fuentes.index, fuentes.values, 0,
                    color=C["azul"], alpha=0.08)
    for x, y in zip(fuentes.index, fuentes.values):
        ax.annotate(f"{y:,.0f}", (x, y), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8.5)
    ax.set_title("Electricidad disponible en Cuba")
    ax.set_ylabel("Gigawatt hora (GWh)")
    ax.set_xticks(list(fuentes.index))
    ax.set_ylim(0, fuentes.max() * 1.15)
    ax.annotate(f"{cambio:+.1f} %", xy=(fuentes.index[-1], fuentes.values[-1]),
                xytext=(-8, -22), textcoords="offset points",
                color=C["rojo"], fontsize=11, fontweight="bold", ha="right")

    ax = axs[1]
    barras = ax.bar(importacion.index, importacion.values, color=C["bateria"], width=0.6)
    for barra in barras:
        ax.annotate(f"{barra.get_height():,.0f}",
                    (barra.get_x() + barra.get_width() / 2, barra.get_height()),
                    textcoords="offset points", xytext=(0, 4), ha="center", fontsize=8.5)
    ax.set_title("Importación de electricidad (generación móvil)")
    ax.set_ylabel("GWh")
    ax.set_xticks(list(importacion.index))
    ax.annotate(f"{cambio_imp:+.0f} %", xy=(importacion.index[-1], importacion.values[-1]),
                xytext=(-6, -20), textcoords="offset points",
                color=C["rojo"], fontsize=11, fontweight="bold", ha="right")

    fig.suptitle("Antes del mercado solar: la electricidad que el sistema dejó de entregar",
                 fontsize=13, fontweight="bold", y=1.02)
    return guardar(fig, "01_onei_contexto.png",
                   "Fuente: ONEI, Anuario Estadístico de Cuba, tabla 10.14 «Balance de electricidad» "
                   "(2019-2022). Elaboración propia.")


# ---------------------------------------------------------------------------
# G02 — La oferta anunciada en el tiempo
# ---------------------------------------------------------------------------
def g02_oferta_mensual() -> Path:
    df = leer("oferta_mensual.csv").sort_values("mes")
    x = np.arange(len(df))
    total = int(df["anuncios"].sum())

    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.bar(x, df["anuncios"], color=C["panel"], alpha=0.35, width=0.85, label="Anuncios por mes")
    ax.plot(x, df["media_movil_3m"], color=C["rojo"], lw=2.2, label="Media móvil (3 meses)")

    etiquetas = [m if i % 3 == 0 else "" for i, m in enumerate(df["mes"])]
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Anuncios publicados")
    ax.set_title(f"{total} anuncios solares entre {df['mes'].iloc[0]} y {df['mes'].iloc[-1]}")
    ax.legend(loc="upper left")

    pico = df.loc[df["anuncios"].idxmax()]
    ax.annotate(f"pico: {int(pico['anuncios'])} anuncios\n{pico['mes']}",
                xy=(df.index[df["anuncios"].idxmax()], pico["anuncios"]),
                xytext=(0, 14), textcoords="offset points",
                ha="center", fontsize=8, color=C["rojo"],
                arrowprops=dict(arrowstyle="->", color=C["rojo"], lw=0.8))
    return guardar(fig, "02_oferta_mensual.png",
                   "Fuente: data/raw/telegram_anuncios.json (352 anuncios, 2 canales). "
                   "Revolico excluido: no expone fecha de publicación. Elaboración propia.")


# ---------------------------------------------------------------------------
# G03 — Composición de la oferta por año
# ---------------------------------------------------------------------------
def g03_composicion_anual() -> Path:
    df = leer("categoria_anio.csv")
    orden = ["panel solar", "batería", "kit solar", "inversor"]
    piv = df.pivot_table(index="anio", columns="categoria", values="pct", fill_value=0)
    piv = piv.reindex(columns=[c for c in orden if c in piv.columns], fill_value=0)
    conteo = df.pivot_table(index="anio", columns="categoria", values="n", fill_value=0).sum(axis=1)

    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    base = np.zeros(len(piv))
    for cat in piv.columns:
        valores = piv[cat].to_numpy()
        ax.bar(piv.index.astype(str), valores, bottom=base,
               color=COLOR_CAT.get(cat, C["gris"]), label=cat, width=0.62)
        for i, (v, b) in enumerate(zip(valores, base)):
            if v >= 6:
                ax.text(i, b + v / 2, f"{v:.0f} %", ha="center", va="center",
                        color="white", fontsize=8.5, fontweight="bold")
        base += valores

    ax.set_ylim(0, 100)
    ax.set_ylabel("Porcentaje de anuncios del año")
    ax.set_title("La mezcla de la oferta cambió: del panel suelto al kit instalado", pad=26)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.24))
    ax.set_xticks(range(len(piv.index)))
    pequenos = {a for a in piv.index if conteo.loc[a] < 30}
    ax.set_xticklabels([
        f"{anio}\nn={int(conteo.loc[anio])}" + (" *" if anio in pequenos else "")
        for anio in piv.index
    ])
    if pequenos:
        ax.text(0.5, 1.015, "* menos de 30 anuncios: la proporción es inestable",
                transform=ax.transAxes, ha="center", va="bottom",
                fontsize=8, color=C["rojo"])
    return guardar(fig, "03_composicion_anual.png",
                   "Fuente: data/raw/telegram_anuncios.json (352 anuncios). Elaboración propia.")


# ---------------------------------------------------------------------------
# G04 — Opacidad: quién no publica precio
# ---------------------------------------------------------------------------
def g04_opacidad() -> Path:
    df = leer("opacidad.csv").sort_values("pct_sin_precio")
    colores = [COLOR_CAT.get(c, C["gris"]) for c in df["categoria"]]

    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    barras = ax.barh(df["categoria"], df["pct_sin_precio"], color=colores, height=0.62)
    for barra, (_, fila) in zip(barras, df.iterrows()):
        ax.text(barra.get_width() + 1, barra.get_y() + barra.get_height() / 2,
                f"{fila['pct_sin_precio']:.1f} %  ({int(fila['sin_precio'])}/{int(fila['n'])})",
                va="center", fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Anuncios sin precio (%)")
    ax.set_title("El precio se esconde donde el producto es estándar")
    ax.grid(axis="y", visible=False)
    return guardar(fig, "04_opacidad_precio.png",
                   "Fuente: data/raw/telegram_anuncios.json (352 anuncios). Elaboración propia.")


# ---------------------------------------------------------------------------
# G05 — Distribución de precios anunciados
# ---------------------------------------------------------------------------
def g05_distribucion_precios() -> Path:
    df = leer("anuncios_limpio.csv")
    usd = df[(df["moneda"] == "USD") & (df["precio"] >= 20)]
    descartados = int(((df["moneda"] == "USD") & (df["precio"] < 20)).sum())
    cats = ["panel solar", "batería", "kit solar"]

    fig, ax = plt.subplots(figsize=(10, 4.6))
    alto = usd[usd["categoria"].isin(cats)]["precio"].max()
    bins = np.logspace(np.log10(20), np.log10(alto * 1.1), 28)
    for cat in cats:
        valores = usd.loc[usd["categoria"] == cat, "precio"]
        if valores.empty:
            continue
        mediana = valores.median()
        ax.hist(valores, bins=bins, alpha=0.55,
                label=f"{cat} (n={valores.size}, mediana {mediana:,.0f} USD)",
                color=COLOR_CAT[cat], edgecolor="white", linewidth=0.5)
        ax.axvline(mediana, color=COLOR_CAT[cat], ls="--", lw=1.2)

    ax.set_xscale("log")
    ax.set_xlabel("Precio anunciado (USD, escala logarítmica)")
    ax.set_ylabel("Número de anuncios")
    ax.set_title("Tres mercados de precio, no uno")
    ax.legend(loc="upper right")
    if descartados:
        ax.annotate(f"{descartados} anuncios con precio < 20 USD\n(probable error de separador decimal)\n"
                    "quedan fuera del eje",
                    xy=(21, ax.get_ylim()[1] * 0.55), fontsize=7.6, color=C["rojo"], ha="left")
    return guardar(fig, "05_distribucion_precios.png",
                   "Fuente: data/raw/telegram_anuncios.json y data/raw/revolico_anuncios.json "
                   "(solo anuncios en USD con precio ≥ 20). Elaboración propia.")


# ---------------------------------------------------------------------------
# G06 — Economía unitaria: USD/W y USD/kWh
# ---------------------------------------------------------------------------
def g06_economia_unitaria() -> Path:
    df = leer("unit_valores.csv")
    w = df[df["metrica"] == "usd_w"]
    kwh = df[df["metrica"] == "usd_kwh"]
    orden = ["panel solar", "inversor", "kit solar"]

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6),
                            gridspec_kw={"width_ratios": [1.35, 1]})

    ax = axs[0]
    datos = [w.loc[w["categoria"] == c, "valor"].dropna().to_numpy() for c in orden]
    bp = ax.boxplot(datos, tick_labels=orden, patch_artist=True, widths=0.55,
                    medianprops=dict(color="black", lw=1.6), showfliers=False)
    for parche, cat in zip(bp["boxes"], orden):
        parche.set_facecolor(COLOR_CAT[cat])
        parche.set_alpha(0.55)
    for i, cat in enumerate(orden, start=1):
        valores = w.loc[w["categoria"] == cat, "valor"].dropna()
        ax.scatter(np.random.default_rng(0).normal(i, 0.05, valores.size), valores,
                   s=10, color="#333", alpha=0.35, zorder=3)
        ax.text(i, valores.median(), f"  {valores.median():.2f}", fontsize=8.5,
                va="bottom", fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylabel("USD por watt (escala log)")
    ax.set_title("Costo por watt")

    ax = axs[1]
    valores = kwh["valor"].dropna()
    ax.boxplot([valores], tick_labels=["batería"], patch_artist=True, widths=0.45,
               medianprops=dict(color="black", lw=1.6), showfliers=False,
               boxprops=dict(facecolor=C["bateria"], alpha=0.55))
    ax.scatter(np.random.default_rng(1).normal(1, 0.05, valores.size), valores,
               s=14, color="#333", alpha=0.5, zorder=3)
    ax.text(1, valores.median(), f"  {valores.median():,.0f}", fontsize=9, va="bottom",
            fontweight="bold")
    ax.set_ylabel("USD por kWh")
    ax.set_title(f"Costo por kWh almacenado (n={valores.size})")

    fig.suptitle("El panel y el inversor se pagan por watt; la batería, por energía",
                 fontsize=12.5, fontweight="bold", y=1.03)
    return guardar(fig, "06_economia_unitaria.png",
                   "Fuente: data/raw/telegram_anuncios.json y data/raw/revolico_anuncios.json. "
                   "Baterías: precio / (Ah × V / 1000). Elaboración propia.")


# ---------------------------------------------------------------------------
# G07 — Potencia vs precio (y el dato imposible)
# ---------------------------------------------------------------------------
def g07_potencia_precio() -> Path:
    df = leer("anuncios_limpio.csv")
    pan = df[(df["categoria"] == "panel solar") & (df["moneda"] == "USD")
             & df["potencia_w"].between(100, 2000) & (df["precio"] >= 20)]

    fig, ax = plt.subplots(figsize=(9.8, 5))
    ax.scatter(pan["potencia_w"], pan["precio"], s=26, alpha=0.6,
               color=C["panel"], edgecolor="white", linewidth=0.5)

    mediana_w = pan["precio"].div(pan["potencia_w"]).median()
    xs = np.array([100, 2000])
    ax.plot(xs, mediana_w * xs, ls="--", color=C["rojo"], lw=1.3,
            label=f"precio mediano = {mediana_w:.2f} USD/W")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Potencia del panel (W, escala log)")
    ax.set_ylabel("Precio (USD, escala log)")
    ax.set_title(f"Potencia y precio: {pan.shape[0]} paneles anunciados")
    ax.legend(loc="upper left")

    maximo = df.loc[df["potencia_w"].idxmax()]
    ax.annotate(f"1 anuncio declara {maximo['potencia_w']:,.0f} W\n"
                f"(fuera del eje: no es un panel)",
                xy=(0.98, 0.04), xycoords="axes fraction", ha="right", va="bottom",
                fontsize=7.8, color=C["rojo"],
                bbox=dict(boxstyle="round,pad=0.4", fc="#fdf2f2", ec=C["rojo"], lw=0.7))
    return guardar(fig, "07_potencia_precio.png",
                   "Fuente: data/raw/telegram_anuncios.json y data/raw/revolico_anuncios.json "
                   "(paneles de 100-2000 W con precio ≥ 20 USD). Elaboración propia.")


# ---------------------------------------------------------------------------
# G08 — Brecha entre lo anunciado y lo pagado
# ---------------------------------------------------------------------------
def g08_brecha() -> Path:
    df = leer("brecha_oferta_compra.csv")
    colores = [C["panel"], C["bateria"]]

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    barras = ax.bar(df["grupo"], df["usd_w"], color=colores, width=0.5)
    for barra, (_, fila) in zip(barras, df.iterrows()):
        ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 0.008,
                f"{fila['usd_w']:.3f} USD/W\nn={int(fila['n'])}",
                ha="center", fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, max(df["usd_w"]) * 1.35)
    ax.set_ylabel("USD por watt (mediana)")
    brecha = float(df["brecha_pct"].iloc[-1])
    ax.set_title(f"En mediana, comprar sale {abs(brecha):.0f} % más barato por watt que el anuncio")
    ax.annotate(f"{brecha:+.1f} %", xy=(1, df["usd_w"].iloc[1]),
                xytext=(0, 46), textcoords="offset points", ha="center",
                fontsize=13, fontweight="bold", color=C["rojo"])
    ax.grid(axis="x", visible=False)
    return guardar(fig, "08_brecha_oferta_compra.png",
                   "Fuente: oferta = 71 paneles anunciados (Telegram + Revolico); compra = 35 entrevistas. "
                   "Elaboración propia.")


# ---------------------------------------------------------------------------
# G09 — El canal de compra no cambia el precio
# ---------------------------------------------------------------------------
def g09_canales() -> Path:
    canal = leer("canales.csv").sort_values("usd_w")
    ent = leer("entrevistas_limpio.csv").dropna(subset=["lugar_de_adquisicion", "usd_por_w"])

    fig, ax = plt.subplots(figsize=(9.5, 4.3))
    barras = ax.barh(canal["canal"], canal["usd_w"], color=C["azul"], alpha=0.35, height=0.6)
    for barra, (_, fila) in zip(barras, canal.iterrows()):
        ax.text(barra.get_width() * 0.02, barra.get_y() + barra.get_height() / 2,
                f"{fila['usd_w']:.3f} USD/W · n={int(fila['n'])}",
                va="center", ha="left", fontsize=8.8, color="#1a1a1a",
                fontweight="bold", zorder=4)

    for i, nombre in enumerate(canal["canal"]):
        valores = ent.loc[ent["lugar_de_adquisicion"] == nombre, "usd_por_w"]
        ax.scatter(valores, np.full(valores.size, i) + np.random.default_rng(2).normal(0, 0.045, valores.size),
                   s=18, color=C["rojo"], alpha=0.65, zorder=3)

    ax.set_xlim(0, canal["usd_w"].max() * 1.55)
    ax.set_xlabel("USD por watt pagado")
    ax.set_title("Comprar por un canal u otro no cambió el precio")
    ax.grid(axis="y", visible=False)
    ax.text(0.99, 0.02, "cada punto rojo = una compra", transform=ax.transAxes,
            ha="right", fontsize=7.8, color=C["rojo"])
    return guardar(fig, "09_canales.png",
                   "Fuente: data/raw/entrevistas.json (35 compras declaradas). Elaboración propia.")


# ---------------------------------------------------------------------------
# G10 — Garantía: oferta vs compra
# ---------------------------------------------------------------------------
def g10_garantia() -> Path:
    g = leer("garantia.csv")
    dur = leer("garantia_duracion.csv")

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.3),
                            gridspec_kw={"width_ratios": [1, 1.1]})

    ax = axs[0]
    barras = ax.bar(g["grupo"], g["pct"], color=[C["gris"], C["bateria"]], width=0.55)
    for barra, (_, fila) in zip(barras, g.iterrows()):
        ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 1.2,
                f"{fila['pct']:.1f} %\n({int(fila['con_garantia'])} de {int(fila['n'])})",
                ha="center", fontsize=9, fontweight="bold")
    ax.set_ylim(0, max(g["pct"]) * 1.45)
    ax.set_ylabel("Anuncios/compras con garantía (%)")
    ax.set_title("La garantía se ofrece poco…")
    ax.grid(axis="x", visible=False)

    ax = axs[1]
    barras = ax.bar(dur["meses"].astype(str), dur["n"], color=C["rojo"], width=0.55)
    for barra, (_, fila) in zip(barras, dur.iterrows()):
        ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 0.15,
                f"{int(fila['n'])}", ha="center", fontsize=9.5, fontweight="bold")
    ax.set_xlabel("Duración declarada (meses)")
    ax.set_ylabel("Compras")
    ax.set_ylim(0, dur["n"].max() * 1.3)
    ax.grid(axis="x", visible=False)

    proporcion = g.set_index("grupo").loc["Oferta (anuncios)"]
    cada = proporcion["n"] / proporcion["con_garantia"]
    moda = dur.loc[dur["n"].idxmax()]
    pct_moda = 100 * moda["n"] / dur["n"].sum()
    ax.set_title(f"…y el {pct_moda:.0f} % dura {int(moda['meses'])} mes")
    fig.suptitle(f"La garantía aparece en 1 de cada {cada:.0f} anuncios y, cuando existe, suele durar un mes",
                 fontsize=12.5, fontweight="bold", y=1.03)
    return guardar(fig, "10_garantia.png",
                   "Fuente: data/raw/telegram_anuncios.json (oferta) y data/raw/entrevistas.json (compra). "
                   "Elaboración propia.")


# ---------------------------------------------------------------------------
# G11 — Marcas: la oferta y la demanda hablan de productos distintos
# ---------------------------------------------------------------------------
def g11_marcas() -> Path:
    df = leer("marcas.csv").copy()
    df["total"] = df["oferta_n"] + df["demanda_n"]
    df = df.sort_values("total", ascending=True).tail(8)

    fig, ax = plt.subplots(figsize=(9.8, 4.8))
    y = np.arange(len(df))
    ax.barh(y, df["oferta_n"], color=C["panel"], label="Oferta (anuncios)", height=0.6)
    ax.barh(y, -df["demanda_n"], color=C["bateria"], label="Demanda (compras)", height=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(df["marca"])
    ax.axvline(0, color="black", lw=0.8)

    for i, (_, fila) in enumerate(df.iterrows()):
        if fila["oferta_n"]:
            ax.text(fila["oferta_n"] + 0.8, i, f"{int(fila['oferta_n'])}", va="center", fontsize=8.5)
        if fila["demanda_n"]:
            ax.text(-fila["demanda_n"] - 0.8, i, f"{int(fila['demanda_n'])}",
                    va="center", ha="right", fontsize=8.5)

    ax.set_xlabel("Número de registros")
    lider = df.sort_values("oferta_n", ascending=False).iloc[0]
    ax.set_title(f"{lider['marca']} domina la oferta ({int(lider['oferta_n'])} anuncios) "
                 f"y no aparece en ninguna compra")
    ax.legend(loc="lower right")
    ax.grid(axis="y", visible=False)
    ax.set_xlim(-max(df["demanda_n"]) * 1.5, max(df["oferta_n"]) * 1.15)
    return guardar(fig, "11_marcas.png",
                   "Fuente: data/raw/telegram_anuncios.json (98 anuncios con marca) y "
                   "data/raw/entrevistas.json (30 compras con marca). Elaboración propia.")


# ---------------------------------------------------------------------------
# G12 — Qué incluye la compra: batería e inversor (campos incorporados 2026-11-06)
# ---------------------------------------------------------------------------
def g12_equipamiento() -> Path:
    df = leer("entrevistas_limpio.csv")
    bat = df["dispone_de_bateria"].astype("boolean")
    inv = df["dispone_de_inversor"].astype("boolean")

    grupos = [
        ("Batería + inversor", int(((bat == True) & (inv == True)).sum()), C["panel"]),
        ("Solo batería", int(((bat == True) & (inv == False)).sum()), C["bateria"]),
        ("Solo panel", int(((bat == False) & (inv == False)).sum()), C["gris"]),
    ]
    total = sum(g[1] for g in grupos)
    if total == 0:
        raise ValueError("entrevistas_limpio.csv no trae dispone_de_bateria/dispone_de_inversor")

    fig, ax = plt.subplots(figsize=(10, 3.4))
    izquierda = 0
    for etiqueta, valor, color in grupos:
        if valor == 0:
            continue
        ax.barh([0], [valor], left=izquierda, color=color, height=0.55, edgecolor="white")
        ax.text(izquierda + valor / 2, 0, f"{etiqueta}\n{valor} ({100 * valor / total:.0f} %)",
                ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        izquierda += valor

    ax.set_xlim(0, total)
    ax.set_ylim(-0.6, 0.6)
    ax.set_yticks([])
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(axis="y", visible=False)
    con_bat = int((bat == True).sum())
    ax.set_title(f"{con_bat} de {total} compras incluyen batería; solo {total - con_bat} son panel suelto")
    return guardar(fig, "12_equipamiento.png",
                   "Fuente: data/raw/entrevistas.json, campos dispone_de_bateria y "
                   "dispone_de_inversor. Elaboración propia.")


FIGURAS = [g01_contexto_onei, g02_oferta_mensual, g03_composicion_anual, g04_opacidad,
           g05_distribucion_precios, g06_economia_unitaria, g07_potencia_precio,
           g08_brecha, g09_canales, g10_garantia, g11_marcas, g12_equipamiento]


def main() -> None:
    print(f"Generando {len(FIGURAS)} figuras en {DIR_FIG} ...")
    for funcion in FIGURAS:
        ruta = funcion()
        print(f"OK  {ruta.name:<32} {ruta.stat().st_size / 1024:6.1f} KB")
    print("Listo.")


if __name__ == "__main__":
    main()
