# MiraiDroid 🤖

Agente de IA autónomo para Android/Termux - Telegram Bot

## Características

- **IA**: MiniMax + Groq (fallback)
- **Voz**: Whisper (Groq API + local)
- **Web Search**: Tavily + DuckDuckGo
- **Plugins**: Calculator, Notes, Translator, System Monitor
- **Comandos**: 90+ comandos integrados
- **Auto-mejora**: Self-patching con validación
- **Rate limiting**: 20 msg/min
- **Crash recovery**: Notificaciones automáticas

## Requisitos

- Python 3.10+
- Android/Termux o cualquier sistema con Python
- Telegram Bot Token
- APIs: MiniMax, Tavily, Groq

## Instalación

```bash
# Clonar
git clone https://github.com/monris-h/MiraiDroid.git
cd MiraiDroid

# Crear .env
cp .env.example .env
# Editar .env con tus credenciales

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python miraidroid.py
```

## Variables .env

```env
TOKEN=tu_telegram_bot_token
MINIMAX_KEY=tu_minimax_api_key
OWNER_ID=tu_telegram_user_id
TAVILY_API_KEY=tu_tavily_api_key
GROQ_API_KEY=tu_groq_api_key
```

## Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar |
| `/help` | Ayuda |
| `/status` | Estado del sistema |
| `/whoami` | Quién soy |
| `/agent_check` | Diagnóstico completo |
| `/search` | Buscar en internet |
| `/restart` | Reiniciar |
| `/ps` | Procesos |
| `/top` | Uso de recursos |
| `/battery` | Batería |
| `/files` | Gestor de archivos |
| `/git_status` | Estado Git |

## Estructura

```
MiraiDroid/
├── miraidroid.py      # Main bot
├── plugins/           # Plugins (auto-load)
├── skills/            # Skills
├── tools/             # Tools
├── tests/             # Tests
├── data/              # Datos (memory, db)
├── logs/              # Logs
├── backups/           # Backups auto
├── downloads/         # Descargas
├── .env.example       # Template credenciales
├── requirements.txt   # Dependencias
├── SOUL.md            # Identidad
├── README.md
└── CHANGELOG.md
```

## Auto-start en Termux

```bash
# Crear servicio
mkdir -p ~/.termux/bash-auto
cat > ~/.termux/bash-auto/miraidroid.sh << 'EOF'
cd ~/agent
python miraidroid.py
EOF

# Hacer ejecutable
chmod +x ~/.termux/bash-auto/miraidroid.sh
```

## Seguridad

- Todas las credenciales en `.env` (nunca en código)
- Owner-only access (solo tú puedes controlar el bot)
- Validación de inputs
- Rate limiting incorporado

## Licencia

MIT

---

*Mirai significa "futuro" en japonés.*
