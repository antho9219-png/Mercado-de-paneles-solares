"""
scraper/telegram_parser.py
==========================
Interpretación y normalización de anuncios de Telegram.

Principios:
- NO inventa datos. Usa null si falta información.
- Distingue paneles individuales vs baterías/inversores/kits.
- Conserva unidades y monedas originales.
- No confunde fecha de extracción con fecha de publicación.
- Documenta ambigüedad en observaciones.
- Filtrado geográfico estricto: solo La Habana con evidencia explícita.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional


# Marcas conocidas
KNOWN_BRANDS = [
    'Longi', 'JinkoSolar', 'Jinko', 'JA Solar', 'AIKO', 'Trina Solar', 'Trina', 
    'Canadian Solar', 'Risen', 'Suntech', 'Astronergy', 'Seraphim', 'Must', 'Bluesun'
]

# Municipios de La Habana
HABANA_MUNICIPIOS = [
    'Playa', 'Plaza de la Revolución', 'Centro Habana', 'Habana Vieja',
    'Regla', 'Habana del Este', 'Guanabacoa', 'San Miguel del Padrón',
    'Diez de Octubre', 'Cerro', 'Marianao', 'La Lisa', 'Boyeros',
    'Arroyo Naranjo', 'Cotorro'
]

# Otras provincias cubanas (para exclusión estricta)
OTHER_PROVINCES = [
    'Matanzas', 'Villa Clara', 'Cienfuegos', 'Sancti Spíritus', 'Ciego de Ávila',
    'Camagüey', 'Las Tunas', 'Holguín', 'Granma', 'Santiago de Cuba',
    'Guantánamo', 'Pinar del Río', 'Artemisa', 'Mayabeque', 'Isla de la Juventud',
    'Cuba'  # solo rechazar si se menciona otra provincia junto con contexto
]


class TelegramParser:
    """Parser para anuncios de paneles solares en mensajes de Telegram."""
    
    def __init__(self):
        # Buscar marcas como palabra completa o como prefijo
        brands_pattern = '|'.join(re.escape(b) for b in sorted(KNOWN_BRANDS, key=len, reverse=True))
        self.brand_pattern = re.compile(r'\b(' + brands_pattern + r')\b', re.IGNORECASE)
        self.brand_prefix_pattern = re.compile(r'\b(' + brands_pattern + r')(?:Solar|Energy|Power)?\b', re.IGNORECASE)
        self.power_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*[Ww](?:att)?s?', re.IGNORECASE)
        self.price_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*(USD|CUP|MLC|€|EUR|\$)', re.IGNORECASE)
        self.panel_count_pattern = re.compile(r'(\d+)\s*(?:panel(?:es)?|módulo(?:s)?)', re.IGNORECASE)
        self.other_province_pattern = re.compile(r'\b(' + '|'.join(re.escape(p) for p in OTHER_PROVINCES) + r')\b', re.IGNORECASE)
        self.warranty_pattern = re.compile(r'garant[ií]a[^.\n]{0,60}', re.IGNORECASE)
        self.life_pattern = re.compile(r'vida\s*[uú]til[^.\n]{0,60}', re.IGNORECASE)
        self.state_pattern = re.compile(r'\b(nuevo|usado|seminuevo|nueva)\b', re.IGNORECASE)
        self.model_pattern = re.compile(r'(?:modelo|serie|model)\s*:?\s*([A-Za-z0-9\-]+)', re.IGNORECASE)
        self.panel_type_pattern = re.compile(r'\b(monocristalino[s]?|policristalino[s]?|bifacial[es]?|portátil[s]?|portatil[s]?|amorfos?)\b', re.IGNORECASE)
        self.battery_type_pattern = re.compile(r'\b(lifepo4|litio|plomo-ácido|plomo acido|gel|AGM|ácido|acido)\b', re.IGNORECASE)
        self.battery_capacity_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*[Aa][Hh]', re.IGNORECASE)
        self.battery_voltage_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*[Vv]', re.IGNORECASE)
        self.battery_energy_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*[Kk][Ww][Hh]', re.IGNORECASE)
        self.inverter_type_pattern = re.compile(r'\b(híbrido|hibrido|on-grid|off-grid|autónomo|autonomo|solar)\b', re.IGNORECASE)
        self.inverter_power_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*[Kk][Ww](?:/[Vv])?', re.IGNORECASE)
    
    def classify_category(self, text: str) -> Optional[str]:
        """Clasifica el anuncio por categoría."""
        text_lower = text.lower()
        
        # Filtrar mensajes que son solo preguntas/solicitudes de compra
        # Si es una pregunta buscando comprar y no ofreciendo vender con detalles de venta
        if re.search(r'¿.*vende|alguien vende|busco.*comprar|necesito comprar', text_lower) and not re.search(r'\bvendo\b|\bventa\b|\bprecio\b.*\d|\d+\s*usd|\d+\s*cup', text_lower):
            # Podría ser pregunta - ser más estricto
            if not re.search(r'\bprecio\s*:|\$\s*\d+|\d+\s*(usd|cup|mlc)', text_lower):
                # Si solo pregunta sin oferta concreta
                if re.search(r'¿.*\?|alguien.*vende|busco|necesito', text_lower) and not re.search(r'\bvendo\b', text_lower):
                    return None
        
        # Kits primero
        if any(k in text_lower for k in ['kit solar', 'kit fotovoltaico', 'sistema solar completo']):
            # No filtrar como pregunta si es anuncio claro con kit
            if re.search(r'¿.*\?|alguien vende|busco|necesito(?!.*vendo)', text_lower) and not re.search(r'\bvendo\b', text_lower) and not re.search(r'\d+\s*(usd|cup|mlc|\$)', text_lower):
                pass  # seguir evaluando
            else:
                if re.search(r'\bvendo\b|\bofrezco\b|\bprecio\b|\ben venta\b', text_lower) or re.search(r'\d+\s*(usd|cup|mlc|\$)', text_lower) or re.search(r'\d+\s*(kw|kwh|w)\b', text_lower):
                    return 'kit solar'
                return 'kit solar'
        # Baterías (solo si no hay paneles)
        if any(b in text_lower for b in ['batería', 'bateria', 'lifepo4', 'litio']) and not re.search(r'\bpanel(?:es)?\b|\bm[oó]dulo(?:s)?\b|\bplaca(?:s)?\b', text_lower):
            if re.search(r'\bvendo\b|\bprecio\b|\bofrezco\b', text_lower) or re.search(r'\d+\s*(ah|v|usd|cup)', text_lower):
                return 'batería'
        # Inversores (solo si no hay paneles)
        if 'inversor' in text_lower and not re.search(r'\bpanel(?:es)?\b|\bm[oó]dulo(?:s)?\b|\bplaca(?:s)?\b', text_lower):
            if re.search(r'\bvendo\b|\bprecio\b|\bofrezco\b', text_lower) or re.search(r'\d+\s*(kw|w|usd|cup)', text_lower):
                return 'inversor'
        # Paneles
        if any(p in text_lower for p in ['panel solar', 'paneles solares', 'módulo solar', 'módulos solares', 'placa solar', 'placas solares']):
            if re.search(r'\bvendo\b|\bprecio\b|\bofrezco\b|\d+\s*usd|\d+\s*cup', text_lower):
                return 'panel solar'
            # Aún puede ser anuncio
            if re.search(r'\d+\s*[Ww]', text_lower) or self.brand_prefix_pattern.search(text) or 'modelo' in text_lower:
                if re.search(r'¿.*alguien vende|busco|necesito(?!.*vendo)', text_lower) and not re.search(r'\bvendo\b', text_lower):
                    # pero si tiene modelo/potencia claro, puede ser anuncio
                    if re.search(r'\d+\s*[Ww]|\bmodelo\b', text_lower):
                        return 'panel solar'
                    return None
                return 'panel solar'
        if re.search(r'\bpanel(?:es)?\b', text_lower) and ('solar' in text_lower or 'fotovolta' in text_lower):
            if re.search(r'\bvendo\b|\d+\s*[Ww]|\d+\s*usd|\bmodelo\b', text_lower):
                return 'panel solar'
        if re.search(r'\bm[oó]dulo(?:s)?\b', text_lower) and ('solar' in text_lower or 'fotovolta' in text_lower):
            if re.search(r'\bvendo\b|\d+\s*[Ww]|\bmodelo\b', text_lower):
                return 'panel solar'
        # Más permisivo: panel/paneles con potencia o marcas conocidas
        if re.search(r'\bpanel(?:es)?\b', text_lower):
            if re.search(r'\d+\s*[Ww]', text_lower) or self.brand_prefix_pattern.search(text) or re.search(r'\bmodelo\b', text_lower):
                if re.search(r'¿.*alguien vende|busco|necesito(?!.*vendo)', text_lower) and not re.search(r'\bvendo\b', text_lower):
                    if re.search(r'\d+\s*[Ww]|\bmodelo\b', text_lower):
                        return 'panel solar'
                    return None
                return 'panel solar'
        if re.search(r'\bm[oó]dulo(?:s)?\b', text_lower):
            if re.search(r'\d+\s*[Ww]', text_lower) or self.brand_prefix_pattern.search(text) or re.search(r'\bmodelo\b', text_lower):
                if re.search(r'¿.*alguien vende|busco|necesito(?!.*vendo)', text_lower) and not re.search(r'\bvendo\b', text_lower):
                    if re.search(r'\d+\s*[Ww]|\bmodelo\b', text_lower):
                        return 'panel solar'
                    return None
                return 'panel solar'
        
        return None
    
    def extract_brand(self, text: str) -> Optional[str]:
        """Extrae marca si está presente."""
        # Primero buscar marcas conocidas con prefijo
        match = self.brand_prefix_pattern.search(text)
        if match:
            brand = match.group(1)
            # Normalizar JinkoSolar a Jinko o mantener como aparece
            if brand.lower() == 'jinkosolar':
                return 'JinkoSolar'
            # Si es Jinko seguido de Solar en el texto original
            if brand.lower() == 'jinko' and re.search(r'jinkosolar', text, re.IGNORECASE):
                return 'JinkoSolar'
            return brand
        match = self.brand_pattern.search(text)
        if match:
            brand = match.group(1)
            if brand.lower() == 'jinkosolar':
                return 'JinkoSolar'
            return brand
        return None
    
    def extract_model(self, text: str) -> Optional[str]:
        """Extrae modelo si está presente."""
        match = self.model_pattern.search(text)
        if match:
            return match.group(1).strip()
        # Intentar patrones adicionales
        m2 = re.search(r'(?:modelo|model)\s+([A-Z0-9][A-Z0-9\-]+)', text, re.IGNORECASE)
        if m2:
            return m2.group(1).strip()
        return None
    
    def extract_power(self, text: str) -> Optional[float]:
        """Extrae potencia en watts."""
        matches = self.power_pattern.findall(text)
        if matches:
            # Tomar el primer valor numérico
            val = matches[0].replace(',', '.')
            try:
                return float(val)
            except ValueError:
                pass
        return None
    
    def extract_price(self, text: str) -> tuple[Optional[float], Optional[str]]:
        """Extrae precio y moneda."""
        match = self.price_pattern.search(text)
        if match:
            val = match.group(1).replace(',', '.')
            curr = match.group(2).upper()
            if curr == '$':
                curr = 'USD'
            elif curr == '€':
                curr = 'EUR'
            try:
                return float(val), curr
            except ValueError:
                pass
        return None, None
    
    def extract_panel_count(self, text: str) -> Optional[int]:
        """Extrae cantidad de paneles."""
        match = self.panel_count_pattern.search(text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
    
    def extract_municipio(self, text: str) -> Optional[str]:
        """Extrae municipio de La Habana si está mencionado."""
        text_lower = text.lower()
        for muni in HABANA_MUNICIPIOS:
            if muni.lower() in text_lower:
                return muni
        return None
    
    def extract_warranty(self, text: str) -> Optional[str]:
        """Extrae información de garantía si está presente."""
        match = self.warranty_pattern.search(text)
        if match:
            return match.group(0).strip()[:120]
        return None
    
    def extract_life(self, text: str) -> Optional[str]:
        """Extrae vida útil si está presente."""
        match = self.life_pattern.search(text)
        if match:
            return match.group(0).strip()[:120]
        return None
    
    def extract_state(self, text: str) -> Optional[str]:
        """Extrae estado si está presente."""
        text_lower = text.lower()
        if re.search(r'\bnuev[oa]s?\b', text_lower):
            return 'nuevo'
        match = self.state_pattern.search(text)
        if match:
            state = match.group(1).lower()
            if state in ['nuevo', 'nueva']:
                return 'nuevo'
            elif state in ['usado']:
                return 'usado'
            elif state == 'seminuevo':
                return 'usado'
        return None

    def extract_panel_type(self, text: str) -> Optional[str]:
        """Extrae tipo de panel si está presente."""
        match = self.panel_type_pattern.search(text)
        if match:
            pt = match.group(1).lower().rstrip('s')
            mapping = {
                'monocristalino': 'Monocristalino',
                'policristalino': 'Policristalino',
                'bifacial': 'Bifacial',
                'portátil': 'Portátil',
                'portatil': 'Portátil',
                'amorfo': 'Amorfo',
            }
            return mapping.get(pt, pt)
        return None

    def extract_battery_type(self, text: str) -> Optional[str]:
        """Extrae tipo de batería si está presente."""
        match = self.battery_type_pattern.search(text)
        if match:
            bt = match.group(1).lower()
            mapping = {
                'lifepo4': 'LiFePO4',
                'litio': 'Li-ion',
                'plomo-ácido': 'Plomo-ácido',
                'plomo acido': 'Plomo-ácido',
                'gel': 'GEL',
                'agm': 'AGM',
                'ácido': 'Plomo-ácido',
                'acido': 'Plomo-ácido',
            }
            return mapping.get(bt, bt.title())
        return None

    def extract_battery_capacity(self, text: str) -> Optional[float]:
        """Extrae capacidad de batería en Ah."""
        match = self.battery_capacity_pattern.search(text)
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except ValueError:
                pass
        return None

    def extract_battery_voltage(self, text: str) -> Optional[float]:
        """Extrae voltaje nominal de batería en V."""
        matches = self.battery_voltage_pattern.findall(text)
        if matches:
            try:
                vals = [float(m.replace(',', '.')) for m in matches]
                return max(vals)  # Tomar el voltaje más alto como nominal
            except ValueError:
                pass
        return None

    def extract_battery_energy(self, text: str) -> Optional[float]:
        """Extrae energía de batería en kWh."""
        match = self.battery_energy_pattern.search(text)
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except ValueError:
                pass
        return None

    def extract_inverter_type(self, text: str) -> Optional[str]:
        """Extrae tipo de inversor si está presente."""
        match = self.inverter_type_pattern.search(text)
        if match:
            it = match.group(1).lower()
            mapping = {
                'híbrido': 'Híbrido',
                'hibrido': 'Híbrido',
                'on-grid': 'On-Grid',
                'off-grid': 'Off-Grid',
                'autónomo': 'Autónomo',
                'autonomo': 'Autónomo',
                'solar': 'Solar',
            }
            return mapping.get(it, it.title())
        return None

    def extract_inverter_power(self, text: str) -> Optional[float]:
        """Extrae potencia nominal de inversor en W."""
        matches = self.inverter_power_pattern.findall(text)
        if matches:
            try:
                vals = [float(m.replace(',', '.')) for m in matches]
                return max(vals) * 1000  # kW a W
            except ValueError:
                pass
        return None
    
    def has_habana_evidence(self, text: str) -> tuple[bool, Optional[str], str]:
        """
        Verifica evidencia geográfica.
        Retorna (incluir, municipio_detectado, clasificacion)
        - incluir=True si es La Habana o sin localidad especificada (según reglas)
        - clasificacion: 'la_habana' o 'sin_localidad_especificada' o 'excluir' o 'requiere_revision'
        """
        text_lower = text.lower()
        
        # Primero verificar si menciona otra provincia explícitamente
        other_match = self.other_province_pattern.search(text)
        if other_match:
            prov_other = other_match.group(1).lower()
            # Si menciona otra provincia y NO menciona explícitamente La Habana junto con contexto que lo invalide
            # Regla: si menciona explícitamente otra provincia distinta a La Habana -> excluir
            if 'la habana' not in text_lower and 'ciudad de la habana' not in text_lower:
                # Verificar si el municipio detectado es realmente de Habana (municipios de Habana no están en otras provincias)
                municipio_cand = self.extract_municipio(text)
                if municipio_cand:
                    # Municipio de Habana encontrado, probablemente es Habana
                    return True, municipio_cand, 'la_habana'
                return False, None, 'excluir'
            else:
                # Menciona ambas - tratar con cuidado, pero si dice La Habana prevalece? 
                # Seguir reglas: si hay mención explícita de otra provincia, ser estricto
                municipio_cand = self.extract_municipio(text)
                if municipio_cand and municipio_cand.lower() in str(HABANA_MUNICIPIOS).lower():
                    # Verificar que municipio pertenece a Habana
                    pass
                # Si hay mención de otra provincia además de La Habana, puede ser ambigüo - marcar para revisión
                # Pero priorizar según instrucciones
                if municipio_cand:
                    return True, municipio_cand, 'la_habana'
                # Menciona La Habana explícitamente
                return True, None, 'la_habana'
        
        # Buscar municipio de La Habana primero
        municipio = self.extract_municipio(text)
        if municipio:
            return True, municipio, 'la_habana'
        
        # Buscar "La Habana" o variaciones
        if re.search(r'\bla\s+habana\b', text_lower) or re.search(r'\bciudad\s+de\s+la\s+habana\b', text_lower):
            return True, None, 'la_habana'
        
        # Sin localidad específica - puede incluirse si es producto relevante
        return False, None, 'sin_localidad_especificada'
    
    def parse_message(self, msg: dict, allow_no_location: bool = False) -> Optional[dict]:
        """Parsea un mensaje de Telegram a formato de anuncio."""
        text = msg.get('text', '')
        if not text or len(text.strip()) < 10:
            return None
        
        category = self.classify_category(text)
        if not category:
            return None
        
        # Verificación geográfica
        geo_result = self.has_habana_evidence(text)
        if len(geo_result) == 3:
            incluir, municipio, clasificacion = geo_result
        else:
            # Compatibilidad con versión anterior
            incluir, municipio = geo_result[0], geo_result[1]
            clasificacion = 'la_habana' if incluir else 'sin_localidad_especificada'
        
        if clasificacion == 'excluir':
            return None
        if not incluir and clasificacion == 'sin_localidad_especificada':
            if not allow_no_location:
                return None  # Por defecto seguir comportamiento estricto para compatibilidad
            # Incluir con localidad/provincia null
            municipio = None
            provincia = None
        elif incluir:
            provincia = 'La Habana' if clasificacion == 'la_habana' else None
        else:
            return None
        
        # Extraer campos comunes
        price, moneda = self.extract_price(text)
        power_w = self.extract_power(text)
        brand = self.extract_brand(text)
        model = self.extract_model(text)
        warranty = self.extract_warranty(text)
        life_util = self.extract_life(text)
        estado = self.extract_state(text) or 'desconocido'
        panel_type = self.extract_panel_type(text)
        
        # Campos específicos por categoría
        panel_count = None
        battery_type = None
        battery_capacity = None
        battery_voltage = None
        battery_energy = None
        inverter_type = None
        inverter_power = None
        
        if category == 'panel solar':
            panel_count = self.extract_panel_count(text)
        elif category == 'batería':
            battery_type = self.extract_battery_type(text)
            battery_capacity = self.extract_battery_capacity(text)
            battery_voltage = self.extract_battery_voltage(text)
            battery_energy = self.extract_battery_energy(text)
        elif category == 'inversor':
            inverter_type = self.extract_inverter_type(text)
            inverter_power = self.extract_inverter_power(text)
        elif category == 'kit solar':
            panel_count = self.extract_panel_count(text)
            battery_type = self.extract_battery_type(text)
            battery_capacity = self.extract_battery_capacity(text)
            battery_energy = self.extract_battery_energy(text)
            inverter_type = self.extract_inverter_type(text)
            inverter_power = self.extract_inverter_power(text)
        
        now = datetime.now(timezone.utc).isoformat()
        msg_date = msg.get('date')
        fecha_publicacion = msg_date.isoformat() if msg_date else None
        
        channel = msg.get('channel', '')
        msg_id = msg.get('id')
        url_mensaje = f"https://t.me/{channel}/{msg_id}" if channel and msg_id else None
        
        observaciones = []
        if category == 'kit solar':
            observaciones.append("Kit solar: distinguir potencia total vs individual")
        elif category == 'panel solar' and panel_count and panel_count > 1:
            observaciones.append("Lote de paneles: verificar potencia individual vs total")
        if category != 'panel solar' and power_w:
            observaciones.append("Categoría diferente a panel individual, potencia puede referirse al equipo completo")
        
        record = {
            'id': None,  # Se asignará después
            'telegram_message_id': msg_id,
            'canal': channel,
            'url_mensaje': url_mensaje,
            'url': url_mensaje,
            'fecha_publicacion': fecha_publicacion,
            'fecha_extraccion': now,
            'categoria': category,
            'categoria_producto': category,
            'tipo': category,
            'marca': brand,
            'modelo': model,
            'potencia_w': power_w if category in ('panel solar', 'kit solar') else None,
            'precio': price,
            'moneda': moneda,
            'municipio': municipio,
            'provincia': provincia if 'provincia' in locals() else ('La Habana' if clasificacion == 'la_habana' else None),
            'localidad': municipio,
            'clasificacion_geografica': clasificacion if clasificacion != 'sin_localidad_especificada' else 'sin_localidad_especificada',
            'estado': estado,
            'garantia': warranty,
            'vida_util': life_util,
            'tipo_panel': panel_type,
            'tipo_bateria': battery_type,
            'marca_bateria': None,
            'modelo_bateria': None,
            'capacidad_ah': battery_capacity,
            'voltaje_nominal_v': battery_voltage,
            'energia_kwh': battery_energy,
            'tipo_inversor': inverter_type,
            'marca_inversor': None,
            'modelo_inversor': None,
            'potencia_inversor_w': inverter_power,
            'incluye_paneles': None,
            'incluye_bateria': None,
            'incluye_inversor': None,
            'componentes_incluidos': None,
            'precio_sistema': None,
            'fuente': 'Telegram',
            'observaciones': '; '.join(observaciones) if observaciones else None
        }
        
        return record
