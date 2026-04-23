# 🤖 TakeovFlow Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/discord.py-2.3%2B-5865F2?style=for-the-badge&logo=discord&logoColor=white"/>
  <img src="https://img.shields.io/badge/Platform-Kali%20%7C%20Ubuntu-557C94?style=for-the-badge&logo=linux&logoColor=white"/>
  <img src="https://img.shields.io/badge/Uso-Bug%20Bounty%20%2F%20Pentest-red?style=for-the-badge"/>
</p>

<p align="center">
  Bot de Discord para detección automática de <b>subdomain takeovers</b>.<br>
  Wrapper interactivo sobre <a href="https://github.com/theoffsecgirl/takeovflow">takeovflow</a> con slash commands, barra de progreso en tiempo real e historial de escaneos.
</p>

---

## 📌 ¿Qué hace este bot?

TakeovFlow Bot integra la herramienta **[takeovflow](https://github.com/theoffsecgirl/takeovflow)** directamente en Discord, permitiéndote lanzar escaneos de subdomain takeover desde cualquier canal sin abrir una terminal. Muestra los resultados con embeds detallados, clasifica los hallazgos por nivel de riesgo (🔴 Crítico / 🟡 Sospechoso) y guarda un historial de los últimos 20 escaneos.

---

## ⚡ Comandos disponibles

| Comando | Descripción |
|--------|-------------|
| `/scan <dominio>` | Escanea un dominio completo buscando subdomain takeovers con barra de progreso en tiempo real |
| `/info <dominio>` | Enumera subdominios del objetivo usando `subfinder` |
| `/historial` | Muestra los últimos 20 dominios escaneados y su resultado |
| `/estado` | Verifica que todas las herramientas necesarias están instaladas |
| `/ayuda` | Lista todos los comandos disponibles |

---

## 🔧 Requisito obligatorio — takeovflow

> ⚠️ **Este bot NO funcionará sin tener instalado [takeovflow](https://github.com/theoffsecgirl/takeovflow).**

Clónalo antes de arrancar el bot:

```bash
git clone https://github.com/theoffsecgirl/takeovflow ~/takeovflow
cd ~/takeovflow
pip install -r requirements.txt
```

El bot espera encontrar `takeovflow.py` en `~/takeovflow/takeovflow.py`.  
Si lo instalas en otro directorio, actualiza la variable `cwd` en `bot.py`.

---

## 🛠️ Instalación completa

### 1. Requisitos previos

- Python `3.10+`
- Go `1.21+`
- Linux (Kali Linux o Ubuntu recomendado)
- Bot de Discord creado en el [Developer Portal](https://discord.com/developers/applications) con scope `bot` + `applications.commands`

### 2. Clona este repositorio

```bash
git clone https://github.com/Borde00/TakeOver-Ds-Bot.git
cd takeovflow-bot
```

### 3. Instala takeovflow ⚠️ obligatorio

```bash
git clone https://github.com/theoffsecgirl/takeovflow ~/takeovflow
pip install -r ~/takeovflow/requirements.txt
```

### 4. Configura el entorno

```bash
cp .env.example .env
nano .env
```

```env
DISCORD_TOKEN=tu_token_aqui
ALLOWED_CHANNEL_ID=id_del_canal_aqui
```

### 5. Arranca el bot

```bash
python3 bot.py
```

---

## 📦 Herramientas requeridas

Usa `/estado` desde Discord para verificar qué tienes instalado.

| Herramienta | Instalación | Uso |
|-------------|-------------|-----|
| [`takeovflow`](https://github.com/theoffsecgirl/takeovflow) | `git clone` (ver arriba) | ⚠️ Motor principal — **obligatorio** |
| `subfinder` | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` | Enumeración de subdominios |
| `assetfinder` | `go install github.com/tomnomnom/assetfinder@latest` | Enumeración adicional |
| `dnsx` | `go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest` | Resolución DNS masiva |
| `httpx` | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` | Verificación HTTP |
| `subjack` | `go install github.com/haccer/subjack@latest` | Detección de takeovers |
| `nuclei` | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` | Templates de vulnerabilidades |
| `dig` | `sudo apt install dnsutils` | Consultas DNS |
| `jq` | `sudo apt install jq` | Procesado de JSON |
| `curl` | `sudo apt install curl` | Peticiones HTTP |

---

## 🔐 Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `DISCORD_TOKEN` | Token del bot de Discord |
| `ALLOWED_CHANNEL_ID` | ID del canal donde se permiten los comandos (`0` = todos) |
| `GUILD_ID` | ID del servidor para sincronizar slash commands (`0` = global) |

## ⚖️ Disclaimer

> Este bot está diseñado para su uso con **fines educativos** o en **entornos aislados y controlados**, así como en programas de **bug bounty** con permiso explícito del objetivo. El uso no autorizado contra sistemas de terceros puede ser **ilegal**. El autor no se hace responsable del mal uso de esta herramienta.

---

<p align="center">
  Este bot se utiliza con fines educativos o en entornos aislados · Powered by <a href="https://github.com/theoffsecgirl/takeovflow">takeovflow</a>
</p>
