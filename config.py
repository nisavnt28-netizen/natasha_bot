# ╔══════════════════════════════════════════════╗
# ║          NATASHA BOT — CONFIG FILE           ║
# ╚══════════════════════════════════════════════╝
# Fill in your actual values below!

# ─── TELEGRAM USERBOT (Your personal account) ──────────────────────────────
# Get these from https://my.telegram.org → "API development tools"
API_ID = 12345678              # <-- apna API ID daalo (int)
API_HASH = "your_api_hash"     # <-- apna API Hash daalo (string)
PHONE_NUMBER = "+91XXXXXXXXXX" # <-- apna phone number (international format)
SESSION_NAME = "natasha_session"  # session file ka naam (kuch bhi)

# ─── GEMINI (Free tier) ────────────────────────────────────────────────────
# Get from https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "your_gemini_api_key"

# ─── OPENROUTER (Fallback) ─────────────────────────────────────────────────
# Get from https://openrouter.ai/keys
OPENROUTER_API_KEY = "your_openrouter_api_key"
# Free models: "mistralai/mistral-7b-instruct:free" or "nousresearch/nous-capybara-7b:free"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"

# ─── YOUR TTS SERVER ───────────────────────────────────────────────────────
# Tera apna server URL — jaise "http://192.168.1.x:5000" ya "https://yourdomain.com"
TTS_SERVER_URL = "http://your-server-url:port"

# ─── POLLINATIONS AI IMAGE GENERATION ─────────────────────────────────────
POLLINATIONS_ENABLED = True  # False karo agar image gen band karni ho

# ─── BOT BEHAVIOR ──────────────────────────────────────────────────────────
# Sirf tab reply karo jab koi Natasha ke message pe reply kare
REPLY_ONLY_MODE = True

# Kitni % chance voice note bhejna (0.0 = kabhi nahi, 1.0 = hamesha)
# 0.4 = 40% messages pe voice note bhi aayegi
VN_CHANCE = 0.4

# Tera Telegram User ID (optional, future features ke liye)
# Find karo: @userinfobot pe /start bhejo
OWNER_ID = 123456789
