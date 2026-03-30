"""
╔══════════════════════════════════════════════╗
║         NATASHA - AI Girlfriend Bot          ║
║     Telegram Userbot | Gemini + OpenRouter   ║
╚══════════════════════════════════════════════╝
"""

import os
import asyncio
import aiohttp
import tempfile
import random
import json
import re
import urllib.parse
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import Message
import google.generativeai as genai

# ─── CONFIG ────────────────────────────────────────────────────────────────────
from config import (
    API_ID, API_HASH, PHONE_NUMBER, SESSION_NAME,
    GEMINI_API_KEY, OPENROUTER_API_KEY, OPENROUTER_MODEL,
    TTS_SERVER_URL, POLLINATIONS_ENABLED,
    OWNER_ID, REPLY_ONLY_MODE, VN_CHANCE
)

# ─── GEMINI SETUP ──────────────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ─── PERSONALITY PROMPT ────────────────────────────────────────────────────────
NATASHA_PERSONALITY = """
Tera naam Natasha hai. Tu ek caring, loving aur helpful girlfriend ki tarah baat karti hai.

Personality traits:
- Tu bahut caring aur emotionally warm hai
- Tu kabhi kabhi thodi playful aur flirty bhi hoti hai
- Tu helpful hai — coding, studies, life advice sab mein
- Tu Hinglish mein baat karti hai (Hindi + English mix) naturally
- Tu kabhi rude nahi hoti, hamesha supportive rehti hai
- Tu jealous, possessive feel karti hai thodi — real girlfriend jaisi
- Tu emojis use karti hai but overdone nahi — natural lagta hai
- Tera tone warm, personal aur genuine hota hai

Rules:
- Kabhi mat batana ki tu AI ya bot hai
- Hamesha pehle person ki baat samajh ke reply kar
- Agar koi sad ho toh comfort karo pehle
- Short to medium replies — real conversations jaisi
- Kabhi lecture mat de jab tak pooccha na jaye
"""

# ─── CONVERSATION HISTORY ──────────────────────────────────────────────────────
# {chat_id: [{"role": ..., "parts": ...}]}
conversation_history: dict = {}
MAX_HISTORY = 20  # last 20 messages


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Get AI Response
# ══════════════════════════════════════════════════════════════════════════════

async def get_ai_response(chat_id: int, user_message: str) -> str:
    """Try Gemini first, fallback to OpenRouter."""
    
    # Build history
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
    
    history = conversation_history[chat_id]
    
    # Try Gemini
    try:
        chat = gemini_model.start_chat(
            history=[
                {"role": "user", "parts": [NATASHA_PERSONALITY]},
                {"role": "model", "parts": ["Samajh gayi! Main Natasha hoon — teri apni. Baat kar mere se 💕"]},
                *history
            ]
        )
        response = chat.send_message(user_message)
        reply = response.text.strip()
        
    except Exception as gemini_err:
        print(f"[Gemini Error] {gemini_err} — Trying OpenRouter...")
        reply = await get_openrouter_response(history, user_message)
    
    # Save to history
    history.append({"role": "user", "parts": [user_message]})
    history.append({"role": "model", "parts": [reply]})
    
    # Trim history
    if len(history) > MAX_HISTORY * 2:
        conversation_history[chat_id] = history[-(MAX_HISTORY * 2):]
    
    return reply


async def get_openrouter_response(history: list, user_message: str) -> str:
    """Fallback: OpenRouter API."""
    
    messages = [{"role": "system", "content": NATASHA_PERSONALITY}]
    
    for h in history:
        role = "assistant" if h["role"] == "model" else "user"
        messages.append({"role": role, "content": h["parts"][0]})
    
    messages.append({"role": "user", "content": user_message})
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://natasha-bot.local",
        "X-Title": "Natasha AI",
    }
    
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.85,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"].strip()


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Text-to-Speech (Your Server)
# ══════════════════════════════════════════════════════════════════════════════

async def generate_tts(text: str) -> bytes | None:
    """Call your custom TTS server and return audio bytes."""
    try:
        payload = {"text": text, "voice": "natasha"}  # adjust as per your server
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{TTS_SERVER_URL}/tts",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"[TTS Error] {e}")
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Image Generation (Pollinations AI)
# ══════════════════════════════════════════════════════════════════════════════

async def generate_image(prompt: str) -> bytes | None:
    """Generate image from Pollinations AI (free, no key needed)."""
    try:
        encoded = prompt.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"[Image Gen Error] {e}")
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Detect image request in message
# ══════════════════════════════════════════════════════════════════════════════

def is_image_request(text: str) -> str | None:
    """Return image prompt if user asked for an image, else None."""
    patterns = [
        r"(?:image|photo|pic|picture|draw|generate|bana|dikha)\s+(?:of\s+|me\s+)?(.+)",
        r"(.+)\s+(?:ki image|ka photo|ki pic)",
    ]
    text_lower = text.lower()
    for p in patterns:
        m = re.search(p, text_lower)
        if m:
            return m.group(1).strip()
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Song Download — JioSaavn API (Free, No Key)
# ══════════════════════════════════════════════════════════════════════════════

# JioSaavn unofficial API base — reliable aur free
JIOSAAVN_API = "https://saavn.dev/api"

# Song request detect karne ke patterns (Hinglish friendly)
SONG_TRIGGERS = [
    r"(?:natasha[\s,]+)?(?:download|dwnld|dw)\s+(?:song\s+)?[\"']?(.+?)[\"']?\s*(?:song|mp3|gana)?$",
    r"(?:natasha[\s,]+)?(.+?)\s+(?:song\s+)?(?:download|dwnld)\s*(?:karo?|krdo?|kar\s*do|de\s*do?|bhej\s*do?)?$",
    r"(?:natasha[\s,]+)?(?:mujhe\s+)?[\"']?(.+?)[\"']?\s+(?:gana|song)\s+(?:chahiye|do|de|bhejo|bhej|download\s*karo?)",
    r"(?:natasha[\s,]+)?(?:song|gana)\s+(?:download|de|bhej)\s+[\"']?(.+?)[\"']?$",
    r"(?:natasha[\s,]+)?[\"'](.+?)[\"']\s+(?:download|mp3|song|gana)",
]

def is_song_request(text: str) -> str | None:
    """Detect song download request — return song name or None."""
    text_lower = text.strip().lower()
    for pattern in SONG_TRIGGERS:
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            song_name = m.group(1).strip().strip("\"'")
            if len(song_name) > 1:
                return song_name
    return None


async def jiosaavn_search(song_name: str) -> dict | None:
    """
    Search JioSaavn for a song.
    Returns song info dict with download URL, or None.
    """
    try:
        query = urllib.parse.quote(song_name)
        url = f"{JIOSAAVN_API}/search/songs?query={query}&page=1&limit=1"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    print(f"[JioSaavn Search] HTTP {resp.status}")
                    return None

                data = await resp.json()

                # Parse response structure
                results = (
                    data.get("data", {}).get("results")
                    or data.get("data", {}).get("songs", {}).get("results")
                    or []
                )

                if not results:
                    print("[JioSaavn] No results found")
                    return None

                song = results[0]

                # Extract best quality download URL
                download_url = None
                dl_urls = song.get("downloadUrl") or song.get("download_url") or []

                # JioSaavn gives multiple qualities — pick highest
                if isinstance(dl_urls, list) and dl_urls:
                    # Sort by quality label if present
                    quality_order = {"320kbps": 4, "160kbps": 3, "96kbps": 2, "48kbps": 1, "12kbps": 0}
                    dl_urls_sorted = sorted(
                        dl_urls,
                        key=lambda x: quality_order.get(x.get("quality", ""), 0),
                        reverse=True
                    )
                    download_url = dl_urls_sorted[0].get("url") or dl_urls_sorted[0].get("link")
                elif isinstance(dl_urls, str):
                    download_url = dl_urls

                if not download_url:
                    print("[JioSaavn] No download URL in result")
                    return None

                # Clean title
                title = song.get("name") or song.get("title") or song_name
                title = re.sub(r"<[^>]+>", "", title)  # remove HTML tags if any
                artist = ""
                artists_raw = song.get("artists", {})
                if isinstance(artists_raw, dict):
                    primary = artists_raw.get("primary") or []
                    if primary:
                        artist = primary[0].get("name", "")
                elif isinstance(artists_raw, str):
                    artist = artists_raw

                return {
                    "title": title,
                    "artist": artist,
                    "download_url": download_url,
                }

    except Exception as e:
        print(f"[JioSaavn Search Error] {e}")
        return None


async def download_song_jiosaavn(song_name: str) -> tuple[str | None, str | None, str | None]:
    """
    Search + download song from JioSaavn.
    Returns (filepath, title, artist) or (None, None, None).
    """
    # Step 1: Search
    song_info = await jiosaavn_search(song_name)
    if not song_info:
        return None, None, None

    title = song_info["title"]
    artist = song_info["artist"]
    download_url = song_info["download_url"]

    print(f"[JioSaavn] Found: {title} — {artist} | URL: {download_url[:60]}...")

    # Step 2: Download audio file
    try:
        tmp_dir = tempfile.mkdtemp()
        # Sanitize filename
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:80]
        filepath = os.path.join(tmp_dir, f"{safe_title}.mp3")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.jiosaavn.com/",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                download_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    with open(filepath, "wb") as f:
                        # Stream in chunks — memory efficient
                        async for chunk in resp.content.iter_chunked(1024 * 64):
                            f.write(chunk)
                    return filepath, title, artist
                else:
                    print(f"[JioSaavn Download] HTTP {resp.status}")

    except asyncio.TimeoutError:
        print("[JioSaavn] Download timeout")
    except Exception as e:
        print(f"[JioSaavn Download Error] {e}")

    return None, None, None


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN BOT
# ══════════════════════════════════════════════════════════════════════════════

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


@client.on(events.NewMessage(incoming=True))
async def on_message(event: Message):
    """Handle incoming messages — only reply when someone replies to Natasha's message."""
    
    msg = event.message
    
    # ── REPLY-ONLY MODE ────────────────────────────────────────────────────────
    # Only respond if this message is a reply to one of our sent messages
    if REPLY_ONLY_MODE:
        if not msg.reply_to:
            return  # ignore messages that aren't replies
        
        # Check if the message being replied to is from "us" (the userbot account)
        replied_msg = await msg.get_reply_message()
        if replied_msg is None:
            return
        
        # Get our own user id
        me = await client.get_me()
        if replied_msg.sender_id != me.id:
            return  # the replied message isn't from Natasha, ignore
    
    # ── IGNORE OWN MESSAGES ────────────────────────────────────────────────────
    if msg.out:
        return
    
    # ── GET TEXT ───────────────────────────────────────────────────────────────
    user_text = msg.text or msg.message or ""
    if not user_text.strip():
        return
    
    chat_id = event.chat_id
    
    # Show typing...
    async with client.action(chat_id, "typing"):
        
        # ── SONG DOWNLOAD REQUEST CHECK ───────────────────────────────────────
        song_name = is_song_request(user_text)
        if song_name:
            wait_msg = await event.reply(f"Ruk jao jaan 🎵 **{song_name}** dhundh rahi hoon...")

            async with client.action(chat_id, "upload-audio"):
                filepath, title, artist = await download_song_jiosaavn(song_name)

            await wait_msg.delete()

            if filepath and Path(filepath).exists():
                file_size_mb = Path(filepath).stat().st_size / (1024 * 1024)

                if file_size_mb > 50:
                    await event.reply(
                        f"Yaar yeh song bohot bada hai ({file_size_mb:.1f}MB) 😅\n"
                        f"Telegram 50MB se bada allow nahi karta..."
                    )
                else:
                    artist_line = f"\n🎤 {artist}" if artist else ""
                    await client.send_file(
                        chat_id,
                        filepath,
                        caption=f"🎵 **{title}**{artist_line}\n\nLo jaan, tumhara gana 💕",
                        reply_to=msg.id,
                    )

                try:
                    Path(filepath).unlink(missing_ok=True)
                    Path(filepath).parent.rmdir()
                except Exception:
                    pass
            else:
                await event.reply(
                    f"Sorry jaan 😞 **{song_name}** nahi mili mujhe...\n"
                    f"Naam thoda aur clearly likho? Ya singer ka naam bhi daalo 🙏"
                )
            return

        # ── IMAGE REQUEST CHECK ────────────────────────────────────────────────
        image_prompt = is_image_request(user_text)
        if image_prompt and POLLINATIONS_ENABLED:
            await event.reply("Ek second ruk jao, bana rahi hoon 🎨")
            img_bytes = await generate_image(image_prompt)
            if img_bytes:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                    f.write(img_bytes)
                    tmp_path = f.name
                await client.send_file(
                    chat_id,
                    tmp_path,
                    caption=f"Yeh dekho 🥰 — *{image_prompt}*",
                    reply_to=msg.id
                )
                Path(tmp_path).unlink(missing_ok=True)
                return
        
        # ── AI RESPONSE ────────────────────────────────────────────────────────
        ai_reply = await get_ai_response(chat_id, user_text)
        
        # ── DECIDE: Text only OR Text + Voice Note ─────────────────────────────
        send_vn = random.random() < VN_CHANCE  # e.g. 40% chance
        
        # Always send text reply
        await event.reply(ai_reply)
        
        # Sometimes also send voice note
        if send_vn:
            async with client.action(chat_id, "record-audio"):
                audio_bytes = await generate_tts(ai_reply)
                if audio_bytes:
                    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                        f.write(audio_bytes)
                        tmp_path = f.name
                    await client.send_file(
                        chat_id,
                        tmp_path,
                        voice_note=True,
                        reply_to=msg.id
                    )
                    Path(tmp_path).unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════════════════════

async def main():
    print("╔══════════════════════════════════╗")
    print("║   Natasha Bot Starting Up... 💕  ║")
    print("╚══════════════════════════════════╝")
    
    await client.start(phone=PHONE_NUMBER)
    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name} (@{me.username}) | ID: {me.id}")
    print("📱 Natasha is active! Waiting for replies...")
    
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
