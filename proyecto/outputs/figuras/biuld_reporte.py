"""
Genera reportaje.html con todas las gráficas embebidas en base64.
Uso: python build_reportaje.py
"""

import base64
import os
from pathlib import Path

FIGURAS_DIR = Path("outputs/figuras")

# Mapa: nombre archivo -> (alt, caption)
FIGURAS = {
    "01_onei_contexto.png": (
        "Gráfico de barras y línea que muestra la evolución de la generación eléctrica total en Cuba entre 2015 y 2022, con una caída visible desde 2019, junto a la participación creciente de las energías renovables.",
        "<strong>Fuente:</strong> ONEI, indicadores de electricidad 2015–2022, y Granma, cobertura de la comparecencia del ministro de Energía y Minas.",
    ),
    "02_oferta_mensual.png": (
        "Gráfico de línea que muestra el número de anuncios de paneles solares por mes en Telegram y Revolico, con picos visibles que coinciden con coyunturas de crisis energética.",
        "<strong>Fuente:</strong> Extracción de anuncios en Telegram y Revolico (n=382).",
    ),
    "03_composicion_anual.png": (
        "Gráfico de barras apiladas que compara el porcentaje de anuncios de paneles sueltos frente a sistemas completos a lo largo del período analizado.",
        "<strong>Fuente:</strong> Clasificación de anuncios (n=382).",
    ),
    "04_opacidad_precio.png": (
        "Gráfico de barras horizontales que contrasta el porcentaje de anuncios que omiten el precio según se trate de paneles sueltos (58 %) o de sistemas completos (9,5 %).",
        "<strong>Fuente:</strong> Análisis de contenido (paneles sueltos n=193, sistemas n=42).",
    ),
    "05_distribucion_precios.png": (
        "Histograma de la distribución del precio por vatio de los paneles solares anunciados, con una mediana marcada en 0,364 dólares por vatio y una cola larga hacia precios altos.",
        "<strong>Fuente:</strong> Anuncios con precio extraíble (n=71).",
    ),
    "08_brecha_oferta_compra.png": (
        "Gráfico de barras que compara el precio mediano anunciado (0,364 USD/W) con el precio mediano realmente pagado por los compradores (0,267 USD/W), evidenciando una brecha del 27 %.",
        "<strong>Fuente:</strong> Anuncios (n=71) y entrevistas (n=35).",
    ),
    "09_canales.png": (
        "Gráfico de barras que muestra la distribución de los 382 anuncios según su canal de origen, con un claro predominio de Telegram sobre Revolico.",
        "<strong>Fuente:</strong> Registro de la fuente de los anuncios (n=382).",
    ),
    "10_garantia.png": (
        "Gráfico que contrasta el bajo porcentaje de anuncios que mencionan garantía (11,9 %) con el alto porcentaje de compradores que dicen haber recibido alguna forma de garantía (51,4 %), mayormente de un mes.",
        "<strong>Fuente:</strong> Anuncios (n=352) y entrevistas (n=35).",
    ),
    "11_marcas.png": (
        "Gráfico de barras comparativo que muestra la presencia de MUST en el 63 % de los anuncios frente a una ausencia total de MUST en las compras efectivas de los 35 entrevistados.",
        "<strong>Fuente:</strong> Mención de marcas en anuncios (n=98) y elección de marca de los compradores (n=35).",
    ),
    "12_consumo_final.png": (
        "Gráfico circular que muestra la proporción de compradores entrevistados que eligieron un sistema completo frente a quienes compraron piezas sueltas, con dominio claro del sistema completo.",
        "<strong>Fuente:</strong> Entrevistas en profundidad (n=35).",
    ),
}


def img_to_data_uri(path: Path) -> str:
    """Convierte una imagen PNG a data URI base64."""
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def build_uri_map() -> dict:
    """Construye el diccionario nombre->data URI, validando existencia y peso."""
    uri_map = {}
    total_mb = 0
    for nombre in FIGURAS:
        ruta = FIGURAS_DIR / nombre
        if not ruta.exists():
            print(f"⚠️  NO ENCONTRADA: {ruta}  (se omitirá del HTML)")
            continue
        uri = img_to_data_uri(ruta)
        tam_mb = len(uri) / (1024 * 1024)
        total_mb += tam_mb
        print(f"✓ {nombre}: {tam_mb:.2f} MB")
        uri_map[nombre] = uri
    print(f"\n📦 Peso total de imágenes embebidas: {total_mb:.2f} MB")
    return uri_map


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>La luz que no llega a la red — Reportaje de datos</title>
<meta name="description" content="Reportaje de datos sobre el mercado informal de paneles solares en La Habana frente a la crisis electroenergética cubana.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&family=Fraunces:opsz,wght@9..144,600;9..144,800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #f7f4ec;
    --surface: #ffffff;
    --ink: #1f2428;
    --ink-soft: #3d4650;
    --ink-muted: #5b6570;
    --accent: #0f766e;
    --accent-strong: #0b5f58;
    --accent-warm: #d97706;
    --rule: #d9d3c4;
    --shadow: 0 10px 30px -18px rgba(15, 30, 30, 0.35);
    --shadow-hover: 0 22px 45px -20px rgba(15, 30, 30, 0.45);
    --radius: 18px;
    --font-base: "Atkinson Hyperlegible", "Segoe UI", system-ui, -apple-system, sans-serif;
    --font-display: "Fraunces", Georgia, "Times New Roman", serif;
    --font-size: 1.125rem;
    --line: 1.7;
    --max: 750px;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; font-size: 100%; }
  body {
    margin: 0;
    background:
      radial-gradient(1200px 600px at 80% -10%, rgba(15, 118, 110, 0.10), transparent 60%),
      radial-gradient(900px 500px at -10% 20%, rgba(217, 119, 6, 0.08), transparent 55%),
      var(--bg);
    color: var(--ink);
    font-family: var(--font-base);
    font-size: var(--font-size);
    line-height: var(--line);
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }
  .skip-link {
    position: absolute; left: -9999px; top: 0;
    background: var(--ink); color: #fff;
    padding: 0.75rem 1rem; z-index: 1000;
    border-radius: 0 0 8px 0;
  }
  .skip-link:focus { left: 0; outline: 3px solid var(--accent-warm); outline-offset: 2px; }
  :focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; border-radius: 4px; }

  .a11y { position: fixed; right: 1rem; bottom: 1rem; display: flex; flex-direction: column; gap: 0.5rem; z-index: 900; }
  .a11y__btn {
    width: 48px; height: 48px; border-radius: 50%;
    border: 1px solid var(--rule); background: var(--surface); color: var(--ink);
    font-family: var(--font-base); font-size: 1.15rem; font-weight: 700;
    cursor: pointer; box-shadow: var(--shadow);
    transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
    display: grid; place-items: center; line-height: 1;
  }
  .a11y__btn:hover { background: var(--accent); color: #fff; transform: translateY(-2px); box-shadow: var(--shadow-hover); }
  .a11y__btn--reset { font-size: 0.85rem; }

  header.hero { position: relative; padding: clamp(3rem, 8vw, 7rem) 1.25rem clamp(2.5rem, 6vw, 4rem); max-width: 1100px; margin: 0 auto; text-align: left; }
  .hero__kicker {
    display: inline-block; font-size: 0.85rem; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--accent-strong); font-weight: 700;
    border-bottom: 2px solid var(--accent-warm); padding-bottom: 0.35rem; margin-bottom: 1.5rem;
  }
  .hero h1 {
    font-family: var(--font-display); font-weight: 800;
    font-size: clamp(2.1rem, 5.5vw, 3.9rem); line-height: 1.08;
    letter-spacing: -0.015em; margin: 0 0 1.5rem; max-width: 20ch; color: var(--ink);
  }
  .hero h1 em { font-style: italic; color: var(--accent-strong); }
  .hero__summary {
    font-size: clamp(1.15rem, 2.2vw, 1.35rem); line-height: 1.6;
    color: var(--ink-soft); max-width: 62ch;
    border-left: 4px solid var(--accent-warm); padding-left: 1.25rem;
  }
  .hero__summary strong { color: var(--ink); }
  .hero__meta { margin-top: 2rem; font-size: 0.9rem; color: var(--ink-muted); display: flex; flex-wrap: wrap; gap: 0.35rem 1.25rem; }

  main { max-width: var(--max); margin: 0 auto; padding: 0 1.25rem 4rem; }
  section { margin-bottom: clamp(3rem, 7vw, 5rem); }
  h2 {
    font-family: var(--font-display); font-weight: 600;
    font-size: clamp(1.5rem, 3.6vw, 2.15rem); line-height: 1.2;
    letter-spacing: -0.01em; margin: 0 0 1.25rem; color: var(--ink);
    position: relative; padding-top: 1rem;
  }
  h2::before {
    content: ""; position: absolute; top: 0; left: 0;
    width: 56px; height: 4px;
    background: linear-gradient(90deg, var(--accent-warm), var(--accent));
    border-radius: 2px;
  }
  p { margin: 0 0 1.25rem; color: var(--ink-soft); }
  p strong { color: var(--ink); font-weight: 700; }
  .lead { font-size: 1.2rem; line-height: 1.65; color: var(--ink); }

  figure {
    margin: 2.5rem -0.5rem 2rem;
    background: var(--surface); border-radius: var(--radius);
    padding: 1.25rem 1.25rem 1rem;
    box-shadow: var(--shadow); border: 1px solid var(--rule);
    transition: transform .25s ease, box-shadow .25s ease;
  }
  figure:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
  figure img { display: block; width: 100%; max-width: 100%; height: auto; border-radius: 12px; background: #f2efe6; }
  figcaption {
    margin-top: 0.85rem; font-size: 0.95rem; font-style: italic;
    color: var(--ink-muted); line-height: 1.5;
    border-top: 1px dashed var(--rule); padding-top: 0.75rem;
  }
  figcaption strong { font-style: normal; color: var(--ink); }

  .method {
    background: var(--surface); border: 1px solid var(--rule);
    border-left: 6px solid var(--accent); border-radius: 14px;
    padding: clamp(1.5rem, 4vw, 2.25rem); margin-top: 3rem;
  }
  .method h2 { font-size: clamp(1.25rem, 2.8vw, 1.6rem); margin-bottom: 1rem; }
  .method h2::before { display: none; }
  .method p { margin-bottom: 1rem; font-size: 1.02rem; }
  .method p:last-child { margin-bottom: 0; }

  footer {
    border-top: 1px solid var(--rule);
    padding: 2.5rem 1.25rem 4rem;
    text-align: center; color: var(--ink-muted);
    font-size: 0.9rem; max-width: var(--max); margin: 0 auto;
  }
  footer strong { color: var(--ink-soft); }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
    figure:hover { transform: none; }
  }
  @media (max-width: 640px) {
    :root { --font-size: 1.06rem; }
    figure { margin-left: 0; margin-right: 0; padding: 0.9rem; }
    .a11y { right: 0.75rem; bottom: 0.75rem; }
    .a11y__btn { width: 44px; height: 44px; }
  }
  @media (prefers-contrast: more) {
    :root { --bg: #ffffff; --ink: #000000; --ink-soft: #111111; --ink-muted: #222222; --rule: #000000; --accent: #0a5a54; }
  }
</style>
</head>
<body>

<a class="skip-link" href="#contenido">Saltar al contenido principal</a>

<div class="a11y" role="group" aria-label="Controles de accesibilidad del texto">
  <button class="a11y__btn" type="button" id="btn-increase" aria-label="Aumentar el tamaño del texto">A+</button>
  <button class="a11y__btn" type="button" id="btn-decrease" aria-label="Disminuir el tamaño del texto">A−</button>
  <button class="a11y__btn a11y__btn--reset" type="button" id="btn-reset" aria-label="Restablecer el tamaño del texto">A</button>
</div>

<header class="hero">
  <span class="hero__kicker">Reportaje de datos · Energía · Cuba</span>
  <h1>La luz que no llega a la red: <em>cómo los habaneros se están fabricando su propio sol</em></h1>
  <p class="hero__summary">
    La ONEI confirma que la generación eléctrica del país cayó más de un <strong>13 %</strong> entre 2019 y 2022, y el ministro de Energía reconoció ante el Parlamento que Cuba dejó de generar <strong>6.700 GWh</strong> en ese periodo. Mientras el Estado construye <strong>22 parques fotovoltaicos</strong> que aportan <strong>481 MW</strong>, en los márgenes de Telegram y Revolico ha nacido otro mercado: <strong>382 anuncios</strong>, <strong>35 entrevistas</strong> y una pregunta incómoda — ¿cuánto cuesta realmente sobrevivir a un apagón?
  </p>
  <div class="hero__meta">
    <span><strong>Fuentes:</strong> ONEI · Granma · Telegram · Revolico</span>
    <span><strong>Método:</strong> 382 anuncios · 35 entrevistas</span>
  </div>
</header>

<main id="contenido">

  <section aria-labelledby="s1">
    <h2 id="s1">El apagón tiene número: 6.700 gigavatios que nunca llegaron</h2>
    <p class="lead">
      Empecemos por lo que sí está escrito. La ONEI registra que la generación total de Cuba pasó de <strong>21.079 GWh en 2019</strong> a unos <strong>19.350 GWh en 2021</strong>, una contracción de más del 13 % en apenas dos años. En ese mismo periodo, la participación de las renovables subió del <strong>3,9 % al 4,8 %</strong>: un avance real, pero sobre un sistema que se encogía más rápido de lo que la energía limpia podía crecer.
    </p>
    <p>
      El ministro de Energía y Minas, Vicente de la O Levy, lo cuantificó sin ambigüedades en su comparecencia de 2025 recogida por <strong>Granma</strong>: frente a 2019, el país ha dejado de generar <strong>6.700 GWh</strong>. La respuesta oficial se llama sol, con <strong>22 parques nuevos que suman 481 MW</strong> dentro de una meta de <strong>2.000 MW</strong> hacia 2028 y la promesa de ahorrar <strong>750.000 toneladas de combustible importado</strong> al año. Bonito sobre el papel. Pero los apagones no esperan cronogramas.
    </p>
    __FIG_01__
  </section>

  <section aria-labelledby="s2">
    <h2 id="s2">El sol no se compra en cualquier momento: sigue el calendario de la crisis</h2>
    <p>
      Si algo demuestra el conteo mensual de anuncios en canales de Telegram es que este mercado <strong>respira al ritmo de los apagones</strong>. Los picos de oferta no son aleatorios: coinciden con los momentos en que la brecha de generación se agranda o con la llegada de nuevos lotes importados. Es una economía que <strong>espera la coyuntura</strong> — vendedores que suben el stock cuando la ciudad se queda a oscuras y compradores que aprietan el paso cuando el inversor ya no da abasto. Nada de esto aparece en las estadísticas oficiales.
    </p>
    __FIG_02__
  </section>

  <section aria-labelledby="s3">
    <h2 id="s3">Panel suelto o sistema completo: dos formas de entender la resiliencia</h2>
    <p>
      La oferta está partida en dos. Cerca de la mitad de los anuncios vende <strong>solo el panel</strong>, y la otra mitad ofrece <strong>el sistema completo</strong> con inversor, soportes y cableado. Detrás de esa división hay dos habanas: la del que sabe armar un sistema y la del que necesita que se lo entreguen funcionando. Los proyectos oficiales que reporta Granma también van por el paquete cerrado: los módulos de Copextel rondan entre <strong>800 y 1.200 vatios</strong> e incluyen panel, perfiles de aluminio, módulo electrónico y cables. La diferencia es que el Estado no anuncia en Telegram.
    </p>
    __FIG_03__
  </section>

  <section aria-labelledby="s4">
    <h2 id="s4">El precio que no se dice: 58 % de los anuncios de paneles lo esconden</h2>
    <p>
      Aquí empieza el juego. De los <strong>193 anuncios de paneles sueltos, 112 no publican precio</strong> — el 58 %. Los sistemas completos son más transparentes: de 42, solo 4 ocultan la cifra. Esa asimetría no es casual. <strong>Obliga a escribir por privado</strong> antes de saber cuánto cuesta, y en ese mensaje se filtra al comprador bisoño. En un país donde el salario medio estatal ronda los pocos miles de pesos, <strong>preguntar el precio es el primer gasto emocional</strong> de toda esta historia.
    </p>
    __FIG_04__
  </section>

  <section aria-labelledby="s5">
    <h2 id="s5">0,364 dólares por vatio: la mediana que oculta un país de precios distintos</h2>
    <p>
      Cuando el precio aparece, el retrato se nubla más. La mediana entre los <strong>71 anuncios con cifra</strong> es de <strong>0,364 USD por vatio</strong>, pero la dispersión es brutal. La cola larga de la distribución cuenta una verdad incómoda: <strong>"solar" en La Habana no es un producto homogéneo</strong>, es un cajón de sastre donde conviven paneles usados, importaciones nuevas y equipos de dudosa procedencia. Granma, en su cobertura oficial, no publica precios unitarios: solo menciona facilidades de <strong>pago a plazos y créditos de largo plazo</strong>, privilegios que el mercado informal no ofrece.
    </p>
    __FIG_05__
  </section>

  <section aria-labelledby="s6">
    <h2 id="s6">Compran el sistema entero: la urgencia mata el ahorro</h2>
    <p>
      Un hallazgo que da que pensar: de los <strong>35 entrevistados</strong>, la gran mayoría compró un <strong>sistema completo</strong>, no piezas sueltas. Es lo contrario de lo que sugiere la oferta publicitaria. ¿La razón? Con apagones de hasta doce horas, <strong>el riesgo de que las piezas no se hablen entre sí y el tiempo de instalación pesan más que los dólares ahorrados</strong>. En Cuba, donde la improvisación es supervivencia, este dato dice mucho: cuando la luz se va, nadie quiere ser su propio ingeniero.
    </p>
    __FIG_12__
  </section>

  <section aria-labelledby="s7">
    <h2 id="s7">MUST reina en los anuncios y nadie la compra: la marca fantasma</h2>
    <p>
      Aquí está el misterio del mercado. En los <strong>98 anuncios que mencionan marca, MUST domina con el 63 %</strong>. Y sin embargo, <strong>ninguno de los 35 compradores entrevistados adquirió MUST</strong>. La fractura admite varias lecturas: un canal mayorista que inundó la publicidad con un lote, una marca que no genera confianza en el trato privado o simplemente un producto que se anuncia mucho pero se vende poco. Lo llamativo es que <strong>Granma nunca menciona una marca comercial</strong>: los módulos que instala Copextel vienen de <strong>donaciones chinas</strong>. La marca, en el mercado informal, es una categoría casi decorativa.
    </p>
    __FIG_11__
  </section>

  <section aria-labelledby="s8">
    <h2 id="s8">El precio se negocia, y el 27 % que te ahorras es la única política pública</h2>
    <p>
      Los 35 entrevistados pagaron una mediana de <strong>0,267 USD por vatio</strong>, un <strong>27 % por debajo de la mediana anunciada</strong>. En un mercado sin precio público, sin plataforma de garantía y sin protección al consumidor, <strong>la negociación es la única política pública real</strong>. Cada conversación privada es una micro-negociación donde el comprador aprende a leer el silencio del vendedor. No hay Defensoría, no hay hoja de reclamación, no hay reseñas. Solo el regateo.
    </p>
    __FIG_08__
  </section>

  <section aria-labelledby="s9">
    <h2 id="s9">Telegram gana la batalla: el mercado vive donde nadie lo vigila</h2>
    <p>
      <strong>Telegram</strong> concentra el grueso del flujo publicitario. Su mecánica de canales permite al vendedor <strong>operar fuera de la fiscalización pública</strong> y llegar solo a quien ya está buscando. Revolico resiste, pero pierde terreno. Es un mundo paralelo al que describe Granma — distribución oficial por Copextel, instalación a domicilio, crédito bancario —: <strong>uno en la luz, otro en la sombra, los dos sirviendo a la misma gente agotada de apagones</strong>. Y esto importa porque el mercado informal, al no dejar rastro estadístico, <strong>es invisible para cualquier política energética que quiera planificar a partir de datos reales</strong>.
    </p>
    __FIG_09__
  </section>

  <section aria-labelledby="s10">
    <h2 id="s10">La garantía dura un mes, si acaso: la palabra como contrato</h2>
    <p>
      Solo el <strong>11,9 % de los anuncios menciona garantía</strong>. Pero las entrevistas revelan algo más sutil: <strong>el 51,4 % de los compradores dice haber recibido alguna forma de respaldo</strong>, la mayoría de solo <strong>un mes</strong>. En el proyecto oficial, los técnicos de Copextel aseguran que los módulos tienen "una vida útil de hasta 20 años", pero las condiciones de posventa no se detallan en la cobertura de Granma. En el mercado informal, la garantía se parece más a un <strong>aval personal</strong>: "si algo falla, me llamas". Un contrato de confianza en un país donde la confianza es un bien escaso.
    </p>
    __FIG_10__
  </section>

  <section aria-labelledby="s11">
    <h2 id="s11">La resiliencia como sistema operativo: lo que los datos no ven</h2>
    <p>
      Al final, la historia no es solo de paneles ni de precios. Es la historia de un país donde <strong>la generación eléctrica cayó más del 13 %</strong> entre 2019 y 2022, el ministro reconoce <strong>6.700 GWh perdidos</strong> y el Estado promete <strong>2.000 MW solares para 2028</strong> — mientras la gente, sin esperar, ya está instalando los suyos. Los paneles que se venden por Telegram, que entran en una maleta, que se atornillan en un balcón de Centro Habana, <strong>no aparecen en la ONEI ni en el inventario del ministerio</strong>, pero generan. Entender esta transición energética completa exige algo más que datos de red: exige <strong>meterse en esas conversaciones privadas donde el precio no está en el anuncio</strong>. La luz que no llega a la red está llegando, en cambio, a muchos hogares. Y esa es, quizás, la única estadística que no necesita actualización.
    </p>
  </section>

  <section class="method" aria-labelledby="metodo">
    <h2 id="metodo">Nota metodológica</h2>
    <p>
      Este reportaje se apoya en tres capas de datos. <strong>Primera</strong>, los indicadores macroeléctricos de la ONEI (generación total 2015–2022, participación de renovables) y la cobertura sostenida de <strong>Granma</strong> sobre la comparecencia del ministro de Energía y Minas y los proyectos fotovoltaicos oficiales. <strong>Segunda</strong>, la extracción y codificación de <strong>382 anuncios</strong> de paneles y sistemas en Telegram y Revolico, de los cuales 71 permitieron extraer precio y 98 mencionaron marca. <strong>Tercera</strong>, <strong>35 entrevistas</strong> semiestructuradas a compradores habaneros.
    </p>
    <p>
      Las limitaciones son las de todo estudio de mercados informales: la muestra publicitaria no representa el volumen total de transacciones, la muestra de entrevistas tiene sesgo de autoselección — quien acepta hablar puede estar más satisfecho con su compra — y <strong>no existe un puente metodológico que permita cruzar los datos oficiales con los del mercado informal</strong>. Este reportaje no intenta cerrar esa grieta: la convierte en hallazgo.
    </p>
  </section>

</main>

<footer>
  <p><strong>Reportaje de datos</strong> · Paneles solares, apagones y resiliencia en La Habana.</p>
  <p>Fuentes: ONEI · Granma · Telegram · Revolico · 35 entrevistas. Diseño editorial accesible (WCAG 2.1 AA).</p>
</footer>

<script>
  (function () {
    const root = document.documentElement;
    const steps = [0.95, 1, 1.125, 1.25, 1.4, 1.55];
    const baseIdx = 2;
    let idx = baseIdx;
    function apply() {
      root.style.setProperty('--font-size', steps[idx] + 'rem');
      const inc = document.getElementById('btn-increase');
      const dec = document.getElementById('btn-decrease');
      if (inc) inc.disabled = idx >= steps.length - 1;
      if (dec) dec.disabled = idx <= 0;
    }
    document.getElementById('btn-increase').addEventListener('click', function () { if (idx < steps.length - 1) { idx++; apply(); } });
    document.getElementById('btn-decrease').addEventListener('click', function () { if (idx > 0) { idx--; apply(); } });
    document.getElementById('btn-reset').addEventListener('click', function () { idx = baseIdx; apply(); });
    apply();
  })();
</script>

</body>
</html>
"""


def build_html(uri_map: dict) -> str:
    """Reemplaza los marcadores __FIG_XX__ por <figure> con data URIs."""
    # Mapeo marcador -> nombre archivo
    marcadores = {
        "__FIG_01__": "01_onei_contexto.png",
        "__FIG_02__": "02_oferta_mensual.png",
        "__FIG_03__": "03_composicion_anual.png",
        "__FIG_04__": "04_opacidad_precio.png",
        "__FIG_05__": "05_distribucion_precios.png",
        "__FIG_12__": "12_consumo_final.png",
        "__FIG_11__": "11_marcas.png",
        "__FIG_08__": "08_brecha_oferta_compra.png",
        "__FIG_09__": "09_canales.png",
        "__FIG_10__": "10_garantia.png",
    }
    html = HTML_TEMPLATE
    for marcador, nombre in marcadores.items():
        if nombre not in uri_map:
            html = html.replace(marcador, f"<p><em>(Gráfica {nombre} no disponible)</em></p>")
            continue
        alt, caption = FIGURAS[nombre]
        figura = (
            f'<figure>\n'
            f'      <img src="{uri_map[nombre]}" alt="{alt}">\n'
            f'      <figcaption>{caption}</figcaption>\n'
            f'    </figure>'
        )
        html = html.replace(marcador, figura)
    return html


def main():
    print("🔍 Construyendo mapa de imágenes en base64...\n")
    uri_map = build_uri_map()
    if not uri_map:
        print("\n❌ No se encontró ninguna imagen. Verifica FIGURAS_DIR.")
        return
    print("\n🧩 Ensamblando HTML...\n")
    html = build_html(uri_map)
    salida = Path("reportaje.html")
    salida.write_text(html, encoding="utf-8")
    tam_mb = salida.stat().st_size / (1024 * 1024)
    print(f"✅ Generado: {salida.resolve()}")
    print(f"📄 Tamaño final: {tam_mb:.2f} MB")
    print(f"🌐 Ábrelo con doble clic o: open reportaje.html")


if __name__ == "__main__":
    main()