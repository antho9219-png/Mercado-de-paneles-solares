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
    'Canadian Solar', 'Risen', 'Suntech', 'Astronergy', 'Seraphim', 'Must'
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
    
    def classify_category(self, text: str) -> Optional[str]:
        """Clasifica el anuncio por categoría."""
        text_lower = text.lower()
        
        # Kits primero
        if any(k in text_lower for k in ['kit solar', 'kit fotovoltaico', 'sistema solar completo']):
            return 'kit solar'
        # Baterías (solo si no hay paneles)
        if any(b in text_lower for b in ['batería', 'bateria', 'lifepo4', 'litio']) and not re.search(r'\bpanel(?:es)?\b|\bm[oó]dulo(?:s)?\b|\bplaca(?:s)?\b', text_lower):
            return 'batería'
        # Inversores (solo si no hay paneles)
        if 'inversor' in text_lower and not re.search(r'\bpanel(?:es)?\b|\bm[oó]dulo(?:s)?\b|\bplaca(?:s)?\b', text_lower):
            return 'inversor'
        # Paneles
        if any(p in text_lower for p in ['panel solar', 'paneles solares', 'módulo solar', 'módulos solares', 'placa solar', 'placas solares']):
            return 'panel solar'
        if re.search(r'\bpanel(?:es)?\b', text_lower) and ('solar' in text_lower or 'fotovolta' in text_lower):
            return 'panel solar'
        if re.search(r'\bm[oó]dulo(?:s)?\b', text_lower) and ('solar' in text_lower or 'fotovolta' in text_lower):
            return 'panel solar'
        # Más permisivo: panel/paneles con potencia o marcas conocidas
        if re.search(r'\bpanel(?:es)?\b', text_lower):
            if re.search(r'\d+\s*[Ww]', text_lower) or self.brand_prefix_pattern.search(text):
                return 'panel solar'
        if re.search(r'\bm[oó]dulo(?:s)?\b', text_lower):
            if re.search(r'\d+\s*[Ww]', text_lower) or self.brand_prefix_pattern.search(text):
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
    
    def has_habana_evidence(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Verifica evidencia explícita de que la oferta es en La Habana.
        Retorna (es_habana, municipio_detectado)
        """
        text_lower = text.lower()
        
        # Buscar municipio primero
        municipio = self.extract_municipio(text)
        if municipio:
            # Asegurar que no hay otra provincia sin mención de La Habana
            if self.other_province_pattern.search(text) and 'la habana' not in text_lower and municipio.lower() not in text_lower:
                pass  # municipio ya confirma Habana
            return True, municipio
        
        # Buscar "La Habana" o variaciones
        if re.search(r'\bla\s+habana\b', text_lower) or re.search(r'\bciudad\s+de\s+la\s+habana\b', text_lower):
            # Excluir si menciona otra provincia explícitamente sin contexto Habana
            if self.other_province_pattern.search(text):
                other = self.other_province_pattern.search(text)
                if other and 'la habana' not in text_lower:
                    return False, None
            return True, None
        
        return False, None
    
    def parse_message(self, msg: dict) -> Optional[dict]:
        """Parsea un mensaje de Telegram a formato de anuncio."""
        text = msg.get('text', '')
        if not text or len(text.strip()) < 10:
            return None
        
        category = self.classify_category(text)
        if not category:
            return None
        
        # Excluir baterías/inversores sin paneles solares
        if category in ('batería', 'inversor'):
            return None
        
        # Verificación geográfica estricta
        is_habana, municipio = self.has_habana_evidence(text)
        if not is_habana:
            return None
        
        # Para paneles individuales, priorizar
        price, moneda = self.extract_price(text)
        power_w = self.extract_power(text)
        brand = self.extract_brand(text)
        model = self.extract_model(text)
        panel_count = self.extract_panel_count(text)
        warranty = self.extract_warranty(text)
        life_util = self.extract_life(text)
        estado = self.extract_state(text) or 'desconocido'
        
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
            'fecha_publicacion': fecha_publicacion,
            'fecha_extraccion': now,
            'categoria': category,
            'marca': brand,
            'modelo': model,
            'potencia_w': power_w if category in ('panel solar', 'kit solar') else None,
            'cantidad_paneles': panel_count,
            'precio': price,
            'moneda': moneda,
            'municipio': municipio,
            'provincia': 'La Habana',
            'estado': estado,
            'garantia': warranty,
            'vida_util': life_util,
            'descripcion': text[:500] if text else None,  # Limitado
            'observaciones': '; '.join(observaciones) if observaciones else None
        }
        
        return record
