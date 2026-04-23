import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import os
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv

os.environ["PATH"] += os.pathsep + os.path.expanduser("~/go/bin")
os.environ["PATH"] += os.pathsep + "/usr/local/bin"
os.environ["PATH"] += os.pathsep + "/usr/bin"

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID", 0))
GUILD_ID = int(os.getenv("GUILD_ID", 0))
HISTORIAL_FILE = os.path.expanduser("~/bot-discord/historial.json")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ──────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────

def cargar_historial():
    if not os.path.exists(HISTORIAL_FILE):
        return []
    with open(HISTORIAL_FILE, "r") as f:
        return json.load(f)

def guardar_historial(dominio, total_vulnerables):
    historial = cargar_historial()
    historial.append({
        "dominio": dominio,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "vulnerables": total_vulnerables
    })
    historial = historial[-20:]
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(historial, f, indent=2)

def limpiar_dominio(dominio: str) -> str:
    dominio = dominio.strip()
    if dominio.startswith("*."):
        dominio = dominio[2:]
    elif dominio.startswith("*"):
        dominio = dominio[1:]
    return dominio.strip()

def parse_takeover_results(output: str) -> list:
    """
    Soporta todos los formatos de takeovflow:
    🔴 [cname] help.whatnot.com -> whatnot.zendesk.com. [Zendesk]
    🟡 [cname] [www.careers.whatnot.com](https://...) -> ext-cust.squarespace.com. [Squarespace]
    🟡 [cname] [www.careers.whatnot.com](https://...) -> ;; error DNS
    ext-cust.squarespace.com. [Squarespace]
    """
    vulnerables = []
    lines = output.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # Solo líneas con [cname] y emoji de riesgo
        if '[cname]' not in line or ('🔴' not in line and '🟡' not in line):
            i += 1
            continue

        nivel = "🔴 CRÍTICO" if '🔴' in line else "🟡 SOSPECHOSO"

        # Limpiar Markdown [texto](url) → solo el texto
        line_clean = re.sub(r'\[([^\]]+)\]\(https?://[^\)]+\)', r'\1', line)

        # Extraer subdominio entre [cname] y ->
        subdominio_match = re.search(
            r'\[cname\]\s+([a-zA-Z0-9._-]+\.[a-zA-Z]{2,})\s*->',
            line_clean
        )

        # Extraer CNAME entre -> y punto/corchete
        cname_match = re.search(
            r'->\s*([a-zA-Z0-9._-]+\.[a-zA-Z]{2,})\.?\s*[\[\n\r]',
            line_clean
        )

        # Si el CNAME no está en la línea actual (error DNS), buscar en la siguiente
        if not cname_match and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            cname_match = re.search(
                r'^([a-zA-Z0-9._-]+\.[a-zA-Z]{2,})\.?\s*\[',
                next_line
            )

        # Extraer servicio — último [texto] al final de la línea
        servicio_match = re.search(r'\[([^\[\]]+)\]\s*$', line_clean)
        if not servicio_match and i + 1 < len(lines):
            servicio_match = re.search(r'\[([^\[\]]+)\]\s*$', lines[i + 1].strip())

        vulnerables.append({
            "subdominio": subdominio_match.group(1) if subdominio_match else "Desconocido",
            "cname": cname_match.group(1) if cname_match else "N/A",
            "servicio": servicio_match.group(1) if servicio_match else "Desconocido",
            "status": nivel,
            "raw": line.strip()
        })

        i += 1

    return vulnerables

def barra_progreso(segundos: int):
    max_seg = 600
    progreso = min(segundos / max_seg, 1.0)
    bloques_llenos = int(progreso * 20)
    bloques_vacios = 20 - bloques_llenos
    barra = "█" * bloques_llenos + "░" * bloques_vacios
    porcentaje = int(progreso * 100)
    return barra, porcentaje


# ──────────────────────────────────────────
# EVENTOS
# ──────────────────────────────────────────

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID) if GUILD_ID else None
    if guild:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
        print(f"[+] Comandos sincronizados para el servidor {GUILD_ID}")
    else:
        await tree.sync()
        print(f"[+] Comandos sincronizados globalmente")
    print(f"[+] Bot online como {bot.user}")


# ──────────────────────────────────────────
# SYNC MANUAL
# ──────────────────────────────────────────

@bot.command()
async def sync(ctx):
    guild = discord.Object(id=GUILD_ID) if GUILD_ID else None
    if guild:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
    else:
        await tree.sync()
    await ctx.send("✅ Comandos resincronizados correctamente")


# ──────────────────────────────────────────
# /scan
# ──────────────────────────────────────────

@tree.command(name="scan", description="Escanea un dominio en busca de subdomain takeovers")
@app_commands.describe(dominio="Dominio objetivo (ej: empresa.com o *.empresa.com)")
async def scan(interaction: discord.Interaction, dominio: str):

    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.NotFound:
        return

    dominio = limpiar_dominio(dominio)

    if ALLOWED_CHANNEL_ID and interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.followup.send("❌ Usa este comando en el canal correcto.", ephemeral=True)
        return

    if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', dominio):
        await interaction.followup.send("❌ Dominio no válido.", ephemeral=True)
        return

    embed_inicio = discord.Embed(
        title="🔍 Escaneando...",
        description=(
            f"**Dominio:** `{dominio}`\n\n"
            f"`░░░░░░░░░░░░░░░░░░░░` 0%\n\n"
            f"⏱️ Tiempo transcurrido: 0s\n"
            f"🔎 Iniciando escaneo..."
        ),
        color=discord.Color.yellow()
    )
    msg_progreso = await interaction.followup.send(embed=embed_inicio, wait=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            "python3", "takeovflow.py", "-d", dominio,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.expanduser("~/takeovflow"),
            env=os.environ
        )
    except Exception as e:
        await msg_progreso.edit(embed=discord.Embed(
            title="❌ Error",
            description=f"No se pudo iniciar takeovflow: `{e}`",
            color=discord.Color.red()
        ))
        return

    fases = [
        (0,   "🔎 Enumerando subdominios..."),
        (30,  "🌐 Resolviendo DNS..."),
        (90,  "🔗 Comprobando CNAMEs..."),
        (180, "⚙️ Analizando servicios externos..."),
        (300, "🚨 Verificando takeovers..."),
        (420, "📋 Finalizando análisis..."),
    ]
    segundos = 0

    async def actualizar_progreso():
        nonlocal segundos
        while proc.returncode is None:
            await asyncio.sleep(10)
            segundos += 10
            fase_actual = fases[0][1]
            for umbral, texto in fases:
                if segundos >= umbral:
                    fase_actual = texto
            barra, porcentaje = barra_progreso(segundos)
            try:
                await msg_progreso.edit(embed=discord.Embed(
                    title="🔍 Escaneando...",
                    description=(
                        f"**Dominio:** `{dominio}`\n\n"
                        f"`{barra}` {porcentaje}%\n\n"
                        f"⏱️ Tiempo transcurrido: {segundos}s\n"
                        f"{fase_actual}"
                    ),
                    color=discord.Color.yellow()
                ))
            except Exception:
                break

    await asyncio.gather(proc.wait(), actualizar_progreso())

    output = (await proc.stdout.read()).decode("utf-8", errors="ignore")
    vulnerables = parse_takeover_results(output)
    guardar_historial(dominio, len(vulnerables))

    if not vulnerables:
        await msg_progreso.edit(embed=discord.Embed(
            title=f"✅ Sin vulnerabilidades — {dominio}",
            description=f"No se encontraron CNAMEs sospechosos.\n⏱️ Tiempo total: {segundos}s",
            color=discord.Color.green()
        ))
        return

    criticos = sum(1 for v in vulnerables if "CRÍTICO" in v["status"])
    sospechosos = sum(1 for v in vulnerables if "SOSPECHOSO" in v["status"])

    await msg_progreso.edit(embed=discord.Embed(
        title=f"🚨 Escaneo completado — {dominio}",
        description=(
            f"🔴 **Críticos:** {criticos}\n"
            f"🟡 **Sospechosos:** {sospechosos}\n"
            f"⏱️ Tiempo total: {segundos}s"
        ),
        color=discord.Color.red()
    ))

    chunks = [vulnerables[i:i+20] for i in range(0, len(vulnerables), 20)]
    for idx, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=f"🚨 Takeovers — {dominio} (página {idx+1}/{len(chunks)})",
            color=discord.Color.red()
        )
        for item in chunk:
            embed.add_field(
                name=f"⚠️ {item['subdominio']}",
                value=(
                    f"**CNAME:** `{item['cname']}`\n"
                    f"**Servicio:** `{item['servicio']}`\n"
                    f"**Riesgo:** {item['status']}"
                ),
                inline=False
            )
        embed.set_footer(text=f"Total: {len(vulnerables)} ({criticos} críticos, {sospechosos} sospechosos) | takeovflow")
        await interaction.followup.send(embed=embed)


# ──────────────────────────────────────────
# /info
# ──────────────────────────────────────────

@tree.command(name="info", description="Enumera subdominios de un dominio sin chequear takeovers")
@app_commands.describe(dominio="Dominio objetivo (ej: empresa.com o *.empresa.com)")
async def info(interaction: discord.Interaction, dominio: str):

    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.NotFound:
        return

    dominio = limpiar_dominio(dominio)

    if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', dominio):
        await interaction.followup.send("❌ Dominio no válido.", ephemeral=True)
        return

    try:
        proc = await asyncio.create_subprocess_exec(
            "subfinder", "-d", dominio, "-silent",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        subdominios = stdout.decode("utf-8", errors="ignore").strip().splitlines()
    except asyncio.TimeoutError:
        await interaction.followup.send("⏱️ Timeout en la enumeración.")
        return
    except Exception as e:
        await interaction.followup.send(f"❌ Error ejecutando subfinder: `{e}`")
        return

    if not subdominios:
        await interaction.followup.send(f"🔎 No se encontraron subdominios para `{dominio}`.")
        return

    chunks = [subdominios[i:i+30] for i in range(0, len(subdominios), 30)]
    for idx, chunk in enumerate(chunks):
        embed = discord.Embed(
            title=f"🌐 Subdominios de {dominio} (página {idx+1}/{len(chunks)})",
            description="```\n" + "\n".join(chunk) + "\n```",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Total encontrados: {len(subdominios)}")
        await interaction.followup.send(embed=embed)


# ──────────────────────────────────────────
# /historial
# ──────────────────────────────────────────

@tree.command(name="historial", description="Muestra los últimos 20 dominios escaneados")
async def historial(interaction: discord.Interaction):
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.NotFound:
        return

    registros = cargar_historial()
    if not registros:
        await interaction.followup.send("📭 No hay escaneos registrados todavía.")
        return

    embed = discord.Embed(title="📋 Historial de escaneos", color=discord.Color.purple())
    for r in reversed(registros):
        estado = "🚨 Vulnerable" if r["vulnerables"] > 0 else "✅ Limpio"
        embed.add_field(
            name=f"🌐 {r['dominio']}",
            value=f"**Fecha:** {r['fecha']}\n**Resultado:** {estado} ({r['vulnerables']} takeovers)",
            inline=False
        )
    await interaction.followup.send(embed=embed)


# ──────────────────────────────────────────
# /estado
# ──────────────────────────────────────────

@tree.command(name="estado", description="Comprueba que todas las herramientas están instaladas")
async def estado(interaction: discord.Interaction):
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.NotFound:
        return

    herramientas = ["subfinder", "assetfinder", "dnsx", "httpx", "subjack", "nuclei", "dig", "jq", "curl"]
    resultados = {}
    for tool in herramientas:
        ruta = shutil.which(tool)
        resultados[tool] = f"✅ `{ruta}`" if ruta else "❌ No encontrado"

    takeovflow_path = os.path.expanduser("~/takeovflow/takeovflow.py")
    resultados["takeovflow"] = f"✅ `{takeovflow_path}`" if os.path.exists(takeovflow_path) else "❌ No encontrado"

    embed = discord.Embed(title="🛠️ Estado de herramientas", color=discord.Color.blurple())
    descripcion = ""
    for tool, status in resultados.items():
        descripcion += f"{status} — `{tool}`\n"
    embed.description = descripcion
    todas_ok = all("✅" in v for v in resultados.values())
    embed.set_footer(text="✅ Todo listo" if todas_ok else "⚠️ Faltan herramientas por instalar")
    await interaction.followup.send(embed=embed)


# ──────────────────────────────────────────
# /ayuda
# ──────────────────────────────────────────

@tree.command(name="ayuda", description="Muestra todos los comandos disponibles")
async def ayuda(interaction: discord.Interaction):
    try:
        await interaction.response.defer(thinking=True)
    except discord.errors.NotFound:
        return

    embed = discord.Embed(title="📖 Comandos disponibles", color=discord.Color.blurple())
    embed.add_field(name="🔍 `/scan <dominio>`", value="Escanea un dominio completo en busca de subdominios vulnerables a takeover.", inline=False)
    embed.add_field(name="🌐 `/info <dominio>`", value="Enumera todos los subdominios de un dominio usando subfinder.", inline=False)
    embed.add_field(name="📋 `/historial`", value="Muestra los últimos 20 dominios escaneados con su resultado.", inline=False)
    embed.add_field(name="🛠️ `/estado`", value="Comprueba que todas las herramientas necesarias están instaladas.", inline=False)
    embed.add_field(name="📖 `/ayuda`", value="Muestra este mensaje.", inline=False)
    embed.set_footer(text="TakeovFlow Bot — by Borde00")
    await interaction.followup.send(embed=embed)


bot.run(TOKEN)