# MiraiDroid 🤖

> Agente de IA autónomo para Android/Termux — Telegram Bot
> *Mirai significa "futuro" en japonés. Soy presencia, no chatbot.*

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![python-telegram-bot](https://img.shields.io/badge/PTB-21%2B-blue)](https://python-telegram-bot.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-30%2F30_passing-brightgreen)](tests/)

---

## 🚀 Quick Start

```bash
git clone https://github.com/monris-h/MiraiDroid.git
cd MiraiDroid

cp .env.example .env
# Edita .env con tus credenciales (TOKEN, MINIMAX_KEY, OWNER_ID, ...)

pip install -r requirements.txt
python main.py
```

El bot se conecta a Telegram y queda a la espera de mensajes del `OWNER_ID`.

---

## ✨ Características

- **IA multi-proveedor** — MiniMax (primario) + Groq (fallback automático)
- **Voz** — Transcripción con Whisper (Groq API o local)
- **Visión** — Análisis de imágenes vía API vision
- **Búsqueda web** — Tavily (primario) + DuckDuckGo (fallback sin API key)
- **Auto-mejora** — El agente puede modificar su propio código con `ast.parse()` sanity check + backup automático + dry-run
- **Plugins** — Auto-load desde `plugins/` sin reinicio
- **50+ comandos** — System, files, git, docker, AI, web, backup, security, heartbeat, cron
- **Rate limiting** — 20 msg/min por usuario + cooldown de 5s por comando
- **Crash recovery** — Notificación automática al owner con traceback
- **Persistencia** — SQLite (WAL mode) + JSON para memoria y activity log
- **Multiplataforma** — Android/Termux, Windows, Linux

---

## 🧱 Stack técnico

| Componente | Versión |
|---|---|
| Python | 3.10+ |
| python-telegram-bot | 21+ (API 8.x) |
| aiohttp | 3.10+ (async HTTP) |
| cryptography | 43+ (Fernet encryption) |
| Pillow | 10.4+ (image processing) |
| simpleeval | 1.0+ (safe arithmetic) |
| SQLite | 3.x (WAL mode, built-in) |

---

## 📦 Instalación

### Requisitos
- Python 3.10 o superior
- Token de [@BotFather](https://t.me/BotFather) en Telegram
- API keys: MiniMax (obligatorio), Groq + Tavily (recomendados)

### Pasos
```bash
# 1. Clonar
git clone https://github.com/monris-h/MiraiDroid.git
cd MiraiDroid

# 2. Configurar credenciales
cp .env.example .env
nano .env  # Edita TOKEN, OWNER_ID, MINIMAX_KEY, etc.

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

### Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `TOKEN` | ✅ | Token del bot de @BotFather |
| `OWNER_ID` | ✅ | Tu Telegram user ID (de @userinfobot) |
| `MINIMAX_KEY` | ✅ | API key de MiniMax |
| `GROQ_API_KEY` | ⚠️ recomendada | API key de Groq (fallback + Whisper) |
| `TAVILY_API_KEY` | ⚠️ recomendada | API key de Tavily (web search) |
| `CRYPTO_KEY` | opcional | Fernet key dedicada para `/encrypt` (si no, se deriva de MINIMAX_KEY) |

---

## 🤖 Comandos principales

### 📊 Info y diagnóstico
| Comando | Descripción |
|---|---|
| `/start` | Mensaje de bienvenida con teclado inline |
| `/help` | Lista completa de comandos |
| `/status` | Estado del sistema + versión + persona |
| `/version` | Solo la versión |
| `/uptime` | Tiempo activo |
| `/agent_check` | Diagnóstico completo (plugins, skills, memory, APIs) |
| `/activity` | Últimas acciones del activity log |
| `/stats` | Estadísticas de uso |

### 🖥️ Sistema
| Comando | Descripción |
|---|---|
| `/ps` | Lista de procesos |
| `/kill <pid>` | Termina un proceso (validado) |
| `/top` | Uso de CPU/memoria |
| `/ping <host>` | Ping a un host (validado) |
| `/dns <domain>` | Resolución DNS |
| `/ports <host> [puertos]` | Escaneo de puertos |
| `/battery` | Estado de batería (Android/Windows) |
| `/apps` | Apps instaladas |

### 📁 Archivos
| Comando | Descripción |
|---|---|
| `/files [path]` | Listar directorio |
| `/read <path>` | Leer archivo |
| `/write <path> <contenido>` | Escribir archivo |
| `/find <pattern>` | Buscar por nombre |

### 🐱 Git / Docker
| Comando | Descripción |
|---|---|
| `/git_status` | Estado del repo |
| `/git_pull` / `/git_commit` / `/git_push` / `/git_log` | Operaciones git |
| `/docker_ps` / `/docker_stats` / `/docker_logs` | Monitoreo Docker |

### 🧠 AI y aprendizaje
| Comando | Descripción |
|---|---|
| `/persona [nombre]` | Cambiar estilo de respuesta (default/technical/casual/formal) |
| `/learn <wrong> → <correct>` | Enseñar correcciones |
| `/forget` | Olvidar todo el aprendizaje |
| `/improve <archivo> <request>` | Auto-mejora del código (con backup) |
| `/exec_code python <código>` | Ejecutar Python (sandbox) |
| `/exec_code bash <código>` | Ejecutar shell (owner only) |

### 🌐 Web y datos
| Comando | Descripción |
|---|---|
| `/search <query>` | Búsqueda en internet |
| `/weather <location>` | Clima actual |
| `/rss <url>` | Feed RSS |
| `/summarize <url>` | Resumir página web |
| `/shorten <url>` | Acortador de URLs |
| `/paste <contenido>` / `/getpaste <code>` | Pastebin local |

### 💓 Heartbeat & cron
| Comando | Descripción |
|---|---|
| `/heartbeat` | Forzar un heartbeat |
| `/heartbeat_on` / `/heartbeat_off` | Activar/desactivar |
| `/heartbeat_stats` | Incluir stats en el heartbeat |
| `/cron_list` / `/cron_enable` / `/cron_disable` | Gestionar jobs |

### 🔒 Seguridad y backup
| Comando | Descripción |
|---|---|
| `/encrypt <texto>` / `/decrypt <texto>` | Cifrado Fernet |
| `/memory` / `/clear` | Ver/limpiar memoria |
| `/backup` / `/backup_list` / `/rollback <ts>` | Snapshots de código |

> **Tip:** Escribe mensajes naturales sin `/` y el bot intentará interpretarlos (buscar, clima, notas, to-dos, cálculos). Si no entiende, llama al LLM.

---

## 📂 Estructura del proyecto

```
MiraiDroid/
├── src/                       # Core: lógica compartida, sin Telegram
│   ├── __init__.py            # Re-exports centralizados
│   ├── config.py              # Carga .env y credenciales
│   ├── constants.py           # PERSONAS, ALIASES, DIRS, MODELS
│   ├── database.py            # SQLite wrapper (WAL mode, error handling)
│   ├── memory.py              # Memory + ActivityLog (JSON persistence)
│   ├── crypto.py              # Fernet encryption + legacy fallback
│   ├── utils.py               # is_owner, is_windows, owner_only decorator
│   ├── stats.py               # Tracking de uso
│   ├── rate_limiter.py        # 20 msg/min + per-command cooldown
│   ├── system_tools.py        # FileManager, GitManager, ProcessManager, ...
│   ├── plugin_manager.py      # Auto-load de plugins
│   └── skill_manager.py       # Skills del usuario
│
├── services/                  # Lógica de negocio pura (sin Telegram)
│   ├── ai.py                  # MiniMax + Groq + SelfImprover
│   ├── web_search.py          # Tavily + DuckDuckGo
│   ├── heartbeat.py           # Mensajes periódicos al owner
│   ├── scheduler.py           # Cron jobs in-process
│   ├── health.py              # Alertas de disco/RAM
│   ├── backup.py              # Snapshots de código (max 10)
│   ├── code_exec.py           # Ejecuta Python/bash en subprocess
│   ├── weather.py             # wttr.in
│   ├── url_shortener.py       # URL shortener + Pastebin
│   ├── rss.py                 # Feed RSS
│   ├── summarizer.py          # Resume URLs/texto
│   └── reminders.py           # Recordatorios
│
├── handlers/                  # Telegram handlers (capa de transporte)
│   ├── commands.py            # 50+ comandos
│   ├── callbacks.py           # Inline keyboard callbacks
│   ├── messages.py            # Router de mensajes naturales + safe calc
│   ├── documents.py           # File uploads
│   ├── voice.py               # Audio transcription
│   └── errors.py              # Error handler global
│
├── plugins/                   # Auto-loaded al arrancar
│   ├── plugin_base.py         # Clase base para plugins
│   └── (tus plugins aquí)
│
├── tests/                     # Suite de tests (30/30 passing)
│   ├── conftest.py            # Fixtures compartidas
│   ├── test_crypto.py
│   ├── test_database.py
│   ├── test_memory.py
│   ├── test_rate_limiter.py
│   └── test_utils.py
│
├── legacy/                    # Código histórico (v5.0.0 monolith, NO USAR)
│   └── miraidroid_legacy.py
│
├── data/                      # Runtime: memory.json, stats.json, *.db
├── backups/                   # Snapshots de código
├── downloads/                 # Archivos recibidos por Telegram
├── logs/                      # Logs del bot
│
├── bot.py                     # Assembly del bot (Telegram Application)
├── main.py                    # Entry point
├── SOUL.md                    # Identidad y reglas del agente
├── README.md                  # Este archivo
├── requirements.txt           # Dependencias
└── .env.example               # Plantilla de credenciales
```

---

## 🧪 Tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Por archivo
python tests/test_crypto.py
python tests/test_rate_limiter.py

# Un test específico
python -m pytest tests/test_database.py::test_wal_mode_enabled -v
```

**Cobertura actual:** 30 tests en 5 archivos — `crypto`, `database`, `memory`, `rate_limiter`, `utils`.

**Qué está cubierto:**
- ✅ Cifrado Fernet: roundtrip, IV aleatorio, errores con key incorrecta, Unicode
- ✅ Base de datos: roundtrip, idempotencia, errores SQL, WAL mode activo
- ✅ Memoria: persistencia, truncado de historial, learning, activity log cap
- ✅ Rate limiting: per-user, per-command cooldown, contadores
- ✅ Utils: detección de plataforma, owner check con int/str

**Qué NO está cubierto (mejoras futuras):**
- `services/ai.py`, `services/web_search.py` — requieren API keys (mark con `@pytest.mark.skipif`)
- `src/plugin_manager.py` — necesita fixture de plugins
- Handlers de Telegram — requieren mocks de `Update`/`Context`

---

## 🔒 Seguridad

- ✅ **Credenciales en `.env`** — nunca en código (`.env` está en `.gitignore`)
- ✅ **Owner-only** — cada handler valida `is_owner(update.effective_user.id)`; comparación robusta como `int`
- ✅ **Rate limiting** — 20 msg/min por usuario + cooldown de 5s por comando
- ✅ **Subprocess seguro** — `kill`, `ping`, `dns`, `ports` validan input con regex y usan list-form (no `shell=True`)
- ✅ **`eval()` reemplazado** — `handle_calc` usa shunting-yard parser con whitelist de caracteres (`simpleeval` opcional)
- ✅ **SQLite WAL mode** — concurrencia segura entre handlers y cron
- ✅ **Error isolation** — DB queries retornan `[]` en error en vez de explotar
- ✅ **Auto-mejora con `ast.parse()`** — código que la IA genera se valida antes de escribir
- ✅ **Fernet encryption** — AES-128-CBC + HMAC + timestamp (reemplaza XOR legacy)

---

## 📱 Auto-start en Termux

```bash
mkdir -p ~/.termux/bash-auto
cat > ~/.termux/bash-auto/miraidroid.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/MiraiDroid
python main.py
EOF
chmod +x ~/.termux/bash-auto/miraidroid.sh
```

El bot arrancará automáticamente cada vez que abras Termux.

---

## 🛠️ Auto-mejora del propio código

El bot puede modificar su propio código con `/improve`. La auditoría 2026-07-02 agregó medidas de seguridad:

1. **Backup automático** antes de escribir
2. **`ast.parse()` sanity check** — código inválido se rechaza
3. **Dry-run mode** — previsualiza sin escribir
4. **Rotación** — máximo 10 backups en `backups/`

Ejemplo:
```
/improve bot.py refactoriza build_app para usar un loop sobre COMMAND_REGISTRY
/improve src/ai.py dry-run  # solo muestra preview, no escribe
```

⚠️ **Recomendación:** revisa el diff después de cada `/improve` antes de hacer `/restart`.

---

## 📜 Auditoría 2026-07-02

Se realizó una auditoría de seguridad y refactor que aplicó 20 de 23 mejoras recomendadas:

- **5 commits** en `master` con análisis estático, refactor y tests
- **30/30 tests pasando** (12 nuevos tests + conftest.py)
- **20 items aplicados:** seguridad, calidad, refactor, deps, tests
- **3 items parciales:** documentados en el reporte, no críticos

Para reproducir el análisis en tu propia copia, ver `data/backups/audit-2026-07-02/`.

---

## 🆘 Troubleshooting

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'telegram'` | `pip install -r requirements.txt` |
| `cryptography not installed — Crypto will use legacy XOR fallback` | `pip install cryptography` (deprecation warning) |
| `sqlite3.OperationalError: database is locked` | WAL mode debería prevenirlo. Si persiste: `pip install --upgrade` y reinicia |
| El bot no responde | Verifica `OWNER_ID` en `.env` (debe ser numérico, sin comillas) |
| `python-telegram-bot 21` rompe | API v8.x tiene breaking changes; ver [migration guide](https://docs.python-telegram-bot.org/en/v21.0/telegram.ext.application.html) |

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE) si está presente, o el archivo equivalente.

---

*Mirai significa "futuro" en japonés. Fitting para una IA.* 🤖
