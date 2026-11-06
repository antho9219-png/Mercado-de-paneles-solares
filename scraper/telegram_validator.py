"""
scraper/telegram_validator.py
=============================
Validación, deduplicación y limpieza de anuncios de Telegram.

Esquema simplificado v2: los campos 'descripcion', 'titulo', 'potencia',
'cantidad', 'cantidad_paneles', 'potencia_por_panel_w' y 'potencia_total_w'
han sido eliminados del esquema. 'potencia_w' es el único campo de potencia
general. Esta clase comprueba que los registros no contengan claves obsoletas.
"""
from __future__ import annotations

import json
from typing import Any


# Claves eliminadas del esquema simplificado (no deben aparecer en registros)
REMOVED_KEYS = frozenset({
    'descripcion', 'titulo', 'potencia', 'cantidad', 'cantidad_paneles',
    'potencia_por_panel_w', 'potencia_total_w',
})


class TelegramValidator:
    """Validador para anuncios de Telegram (esquema simplificado)."""
    
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
    
    def removed_keys_present(self, record: dict) -> list[str]:
        """Retorna las claves eliminadas del esquema presentes en el registro."""
        return sorted(REMOVED_KEYS & record.keys())
    
    def is_simplified_schema(self, record: dict) -> bool:
        """Comprueba que el registro cumpla el esquema simplificado."""
        return not self.removed_keys_present(record)
    
    def is_sufficient(self, record: dict) -> tuple[bool, str]:
        """Verifica si el anuncio tiene información suficiente."""
        # Debe tener al menos marca o modelo para identificar el producto.
        # Sin ambos, solo es aceptable si hay precio y categoría (oferta concreta),
        # ya que el campo 'descripcion' fue eliminado del esquema.
        if not record.get('marca') and not record.get('modelo'):
            identificacion = record.get('precio') and (
                record.get('categoria') or record.get('categoria_producto') or record.get('tipo')
            )
            if not identificacion:
                return False, "Sin marca, modelo ni oferta concreta (precio+categoría)"
        
        # Debe tener precio o algún dato técnico para ser útil
        if (not record.get('precio') and not record.get('potencia_w') and 
            not record.get('capacidad_ah') and not record.get('potencia_inversor_w') and
            not record.get('energia_kwh') and not record.get('precio_sistema')):
            return False, "Sin precio ni datos técnicos"
        
        # Debe ser de La Habana o sin localidad especificada (según reglas v2)
        clasif = record.get('clasificacion_geografica')
        prov = record.get('provincia')
        if clasif == 'excluir':
            return False, "Ubicación fuera de ámbito"
        if clasif == 'sin_localidad_especificada':
            # Permitir si no hay provincia otra que Habana
            if prov and prov != 'La Habana':
                return False, "Ubicación fuera de La Habana"
            return True, "OK"
        if prov == 'La Habana' or clasif == 'la_habana':
            return True, "OK"
        if prov is None and clasif == 'sin_localidad_especificada':
            return True, "OK"
        # Para compatibilidad con formato antiguo
        if prov != 'La Habana':
            return False, "Ubicación fuera de La Habana"
        
        return True, "OK"
    
    def validate(self, records: list[dict]) -> dict:
        """Valida y deduplica registros."""
        valid = []
        duplicates = 0
        insufficient = 0
        esquema_obsoleto = 0
        
        for rec in records:
            if self.is_duplicate(rec):
                duplicates += 1
                continue
            
            if not self.is_simplified_schema(rec):
                insufficient += 1
                esquema_obsoleto += 1
                self.errors.append(
                    f"Registro con claves eliminadas del esquema: "
                    f"{self.removed_keys_present(rec)} "
                    f"(canal={rec.get('canal')}, msg={rec.get('telegram_message_id')})"
                )
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
            'esquema_obsoleto': esquema_obsoleto,
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
            f"Con esquema obsoleto (claves eliminadas): {result.get('esquema_obsoleto', 0)}",
            ""
        ]
        return "\n".join(lines)
