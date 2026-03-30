# 💕 NATASHA — AI Girlfriend Telegram Userbot

## Setup Guide (Step by Step)

---

### STEP 1 — Telegram API Credentials lena

1. Ja `https://my.telegram.org`
2. Apna phone number se login karo
3. "API development tools" pe click karo
4. Ek app banao — `App api_id` aur `App api_hash` copy karo
5. `config.py` mein fill karo

---

### STEP 2 — Gemini API Key

1. Ja `https://aistudio.google.com/app/apikey`
2. "Create API Key" — free hai
3. `config.py` mein `GEMINI_API_KEY` fill karo

---

### STEP 3 — OpenRouter API Key (Fallback)

1. Ja `https://openrouter.ai`
2. Sign up → Keys → Create Key
3. Free models available hain (mistral etc.)
4. `config.py` mein fill karo

---

### STEP 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### STEP 5 — Config Fill Karo

`config.py` open karo aur ye sab fill karo:
- `API_ID` — Telegram se
- `API_HASH` — Telegram se
- `PHONE_NUMBER` — "+91XXXXXXXXXX" format mein
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `TTS_SERVER_URL` — tera apna TTS server URL

---

### STEP 6 — Run Karo

```bash
python natasha.py
```

**Pehli baar run karne pe:**
- OTP aayega tera phone pe — enter karo
- Session file ban jaayegi → agli baar automatically login

---

## Bot Kaise Kaam Karta Hai

- **REPLY_ONLY_MODE = True** → Natasha sirf tab reply karegi jab koi **uske message pe reply karega**
- **VN_CHANCE = 0.4** → 40% chance ki voice note bhi aaye sath mein
- **Image generation** → "generate image of sunset" jaisi request pe Pollinations AI se image aayegi

---

## TTS Server Expected Format

Bot tera server pe POST request bhejta hai:

```
POST {TTS_SERVER_URL}/tts
Content-Type: application/json

{
  "text": "Kya hua, theek ho? 💕",
  "voice": "natasha"
}
```

Response: raw audio bytes (OGG/MP3/WAV)

Agar tera server alag format mein hai — `natasha.py` mein `generate_tts()` function adjust karo.

---

## Keep Bot Running (24/7)

**Termux pe:**
```bash
nohup python natasha.py &
```

**Linux server pe:**
```bash
screen -S natasha
python natasha.py
# Ctrl+A D to detach
```

---

## ⚠️ Important Notes

- Yeh **Userbot** hai — tera personal account use hoga
- Telegram ki ToS technically userbot allow karti hai personal use ke liye
- Bot farming ya spam ke liye mat use karna
- Agar account ban ho toh — secondary account banao aur woh use karo
