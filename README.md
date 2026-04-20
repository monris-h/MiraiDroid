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
├── src/                 # Core del proyecto
│   ├── __init__.py      # Exports centralizados
│   ├── config.py        # Carga .env y credenciales
│   ├── constants.py     # PERSONAS, ALIASES, DIRS
│   ├── database.py      # SQLite wrapper
│   ├── memory.py        # Memory + ActivityLog
│   ├── crypto.py        # Encryption
│   ├── utils.py         # is_owner, is_windows, helpers
│   ├── stats.py         # Stats tracking
│   ├── rate_limiter.py  # Rate limiting
│   ├── system_tools.py  # FileManager, GitManager, ProcessManager, etc.
│   ├── plugin_manager.py
│   └── skill_manager.py
├── services/            # Lógica de negocio pura
│   ├── ai.py            # MiniMax + Groq fallback
│   ├── web_search.py    # Tavily + DuckDuckGo
│   ├── heartbeat.py
│   ├── scheduler.py
│   ├── health.py
│   ├── backup.py
│   ├── code_exec.py
│   ├── weather.py
│   ├── url_shortener.py
│   ├── pastebin.py
│   ├── rss.py
│   ├── summarizer.py
│   └── reminders.py
├── handlers/            # Telegram handlers
│   ├── commands.py      # Todos los comandos
│   ├── callbacks.py
│   ├── messages.py      # Router + AI
│   ├── documents.py
│   ├── voice.py
│   └── errors.py
├── plugins/             # Plugins (auto-load)
├── bot.py               # Assembly del bot
├── main.py              # Entry point
├── SOUL.md              # Identidad
├── README.md
├── requirements.txt
└── .env                 # Credenciales (nunca en código)
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
