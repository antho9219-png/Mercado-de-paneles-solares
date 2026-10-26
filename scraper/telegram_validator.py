"""
scraper/telegram_validator.py
============================
Validación, deduplicación y limpieza de anuncios de Telegram.
"""
from __future__ import annotations

import json
from typing import Any


class TelegramValidator:
    """Validador para anuncios de Telegram."""
    
    def __init__(self):
        self.seen = set()
        self.errors = []
    
    def is_duplicate(self, record: dict) -> bool:
        """Detecta duplicados por canal + message_id."""
        key = (record.get('canal'), record.get('telegram_message_id'))
        if key in self.seen:
            return True
        self.seen.add(key)
        return False
    
    def is_sufficient(self, record: dict) -> tuple[bool, str]:
        """Verifica si el anuncio tiene información suficiente."""
        # Debe tener al menos marca o descripción con info útil
        if not record.get('marca') and not record.get('descripcion'):
            return False, "Sin marca ni descripción"
        
        # Debe tener precio o potencia para ser útil
        if not record.get('precio') and not record.get('potencia_w') and not record.get('cantidad_paneles'):
            return False, "Sin precio, potencia o cantidad"
        
        # Debe ser de La Habana
        if record.get('provincia') != 'La Habana':
            return False, "Ubicación fuera de La Habana"
        
        # No aceptar baterías/inversores
        if record.get('categoria') in ('batería', 'inversor'):
            return False, "Solo baterías/inversores sin paneles"
        
        return True, "OK"
    
    def validate(self, records: list[dict]) -> dict:
        """Valida y deduplica registros."""
        valid = []
        duplicates = 0
        insufficient = 0
        
        for rec in records:
            if self.is_duplicate(rec):
                duplicates += 1
                continue
            
            sufficient, reason = self.is_sufficient(rec)
            if not sufficient:
                insufficient += 1
                continue
            
            valid.append(rec)
        
        # Asignar IDs
        for i, rec in enumerate(valid):
            rec['id'] = i + 1
        
        return {
            'records': valid,
            'duplicates': duplicates,
            'insufficient': insufficient,
            'total_processed': len(records),
            'valid': len(valid)
        }
    
    def generate_report(self, result: dict) -> str:
        """Genera reporte de validación."""
        lines = [
            "=== REPORTE DE VALIDACIÓN TELEGRAM ===",
            f"Mensajes procesados: {result['total_processed']}",
            f"Anuncios válidos: {result['valid']}",
            f"Duplicados descartados: {result['duplicates']}",
            f"Insuficientes descartados: {result['insufficient']}",
            ""
        ]
        return "\n".join(lines)
