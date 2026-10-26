# INSTRUCCIONES PARA EJECUTAR EXTRACCIÓN DE TELEGRAM EN WINDOWS 11

## 1. Preparación del entorno

### Abrir terminal
Abre PowerShell o Terminal en la raíz del proyecto:
`C:\Users\Ramsés\Documents\proyecto cd`

### Crear y activar entorno virtual (recomendado)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución de scripts:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Instalar dependencias
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 2. Configurar credenciales de Telegram

### Obtener credenciales
1. Ve a https://my.telegram.org/apps
2. Inicia sesión con tu número de teléfono
3. Crea una aplicación
4. Copia `api_id` y `api_hash`

### Crear archivo .env
Copia `.env.example` a `.env`:
```powershell
Copy-Item .env.example .env
```

Edita `.env` con tus credenciales reales (usa Notepad, VS Code, etc.):
```env
TELEGRAM_API_ID=tu_api_id_aqui
TELEGRAM_API_HASH=tu_api_hash_aqui
TELEGRAM_PHONE=+53XXXXXXXXX
TELEGRAM_SESSION_NAME=mercado_solar_cuba
```

**IMPORTANTE:** `.env` está en `.gitignore` y NUNCA debe subirse al repositorio.

## 3. Configurar canales públicos

Edita `config/telegram_channels.json` con canales públicos verificados:
```json
{
  "channels": [
    {"username": "canal_publico_1"},
    {"username": "canal_publico_2"}
  ]
}
```

- **Sin `@`** al inicio
- **Solo canales públicos** verificables
- **Relevantes para La Habana/Cuba** venta de paneles solares
- **Sin grupos privados**

## 4. Ejecutar extracción

```powershell
python extract_telegram_habana.py
```

### Comportamiento esperado:
- Primera vez: Telethon solicitará código de autenticación en terminal (escríbelo manualmente)
- Se crearán archivos `.session` (ignorados por git)
- Solo extrae anuncios con evidencia explícita de La Habana (municipios o "La Habana")
- Excluye otras provincias, baterías/inversores sin paneles
- Deduplica por canal + ID de mensaje
- Usa `null` para datos faltantes
- NO inventa datos
- Guarda en `data/telegram_paneles_habana.json`

## 5. Verificar resultados

El script mostrará:
- Canales consultados
- Mensajes examinados
- Anuncios parseados con evidencia de La Habana
- Duplicados/insuficientes descartados
- Anuncios válidos de La Habana
- Ruta del archivo generado

## Notas importantes

- Si hay menos de 30 anuncios válidos, se informará el número real
- No se sobrescriben otros archivos de datos
- Respeta límites de API de Telegram
- Solo usa métodos autorizados
- No se modifican `entrevistas.json` ni otros datos ajenos
