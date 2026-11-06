import json
import sys
from datetime import datetime, timezone
sys.path.insert(0, '.')
from scraper.telegram_parser import TelegramParser

parser = TelegramParser()

mensajes = [
    {
        'id': 64, 'channel': 'EquiposSolares',
        'text': '☀️ ¡Aprovecha el poder del sol con JinkoSolar! ⚡\n\n🔥 Paneles Solares JinkoSolar 590W\n✅ Monocristalinos y bifaciales — capturan energía por ambos lados\n✅ Alta eficiencia y durabilidad garantizada\n✅ Ideales para casas, negocios o proyectos solares\n\n💰 Precio 143 USD por unidad. Si desea comprar un Pallets o más se negocia el precio.\n📍 La Habana.\n\n🌎 ¡Invierte en energía limpia y empieza a ahorrar desde hoy!\n\n📲Contáctenos +5363468417',
        'date': '2025-11-10T05:46:58+00:00'
    },
    {
        'id': 7061, 'channel': 'paneles_solares_cuba',
        'text': 'Kit Solar de 12 kW Must\nInversor híbrido Must de 12 kW para la 110/220 v\nBatería de 51.2 v x 300 ah,haciendo 15 kWh de respaldo\n12 paneles Bifaciales de más de 600 watts\nMontaje incluido\nTransfer incluido\nGarantía de seis meses\nTransporte gratis en La Habana,Artemisa y Mayabeque \nPrecio:9700 usd \n(Sistema de alarma incluido 🚨,para la protección de sus paneles).\n\n📱54209533\nWhatsApp 👉🏼https://Wa.me/+5354209533',
        'date': '2026-10-14T10:59:19+00:00'
    },
    {
        'id': 5484, 'channel': 'paneles_solares_cuba',
        'text': 'Paneles Solares Seraphim Serie Sable Bifaciales 620W – Máxima Potencia y Rendimiento. Minorista $195 / Mayorista $177 USD\nLa Lisa, La Habana 58058531  -  50974409',
        'date': '2026-09-08T06:08:38+00:00'
    },
    {
        'id': 5482, 'channel': 'paneles_solares_cuba',
        'text': 'Paneles Solares Seraphim Serie Sable Bifaciales 620W – Máxima Potencia y Rendimiento. Minorista $195 / Mayorista $177 USD\nLa Lisa, La Habana 58058531  -  50974409',
        'date': '2026-09-08T05:54:05+00:00'
    },
    {
        'id': 5464, 'channel': 'paneles_solares_cuba',
        'text': 'Paneles Solares Longi Monocristalino 650W\nPrecio: 250 usd\nAceptamos: usd, euro y cup 10 pesos por encima del toque \n📍Playa\n🚙Mensajería por costo adicional \n\n📱54209533\nWhatsApp 👉🏽 https://Wa.me/+5354209533',
        'date': '2026-09-02T22:31:23+00:00'
    }
]

# Convertir fechas de string a datetime
for msg in mensajes:
    if isinstance(msg['date'], str):
        msg['date'] = datetime.fromisoformat(msg['date'])

for i, msg in enumerate(mensajes):
    rec = parser.parse_message(msg)
    print(f'=== Mensaje {msg["id"]} ({msg["channel"]}) ===')
    if rec:
        for k, v in rec.items():
            if v is not None:
                # Sanitizar para salida de consola Windows
                s = str(v)
                try:
                    print(f'  {k}: {s.encode("cp1252", errors="replace").decode("cp1252")}')
                except Exception:
                    print(f'  {k}: [valor con caracteres especiales]')
    else:
        print('  No se pudo parsear')
    print()
