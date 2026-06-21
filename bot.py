import os, io, subprocess, re
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from PIL import Image

TOKEN = "8839915273:AAG-iAMNlAsfY5do3osEOO285kZ9tThBlLc"

DENIED_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"dd\s+if=",
    r"mkfs",
    r"shutdown",
    r"reboot",
    r"poweroff",
    r"halt",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\};",
    r"chmod\s+777\s+/",
    r"chown\s+-R\s+[^ ]+\s+/",
    r">\s*/dev/",
    r"curl.*\|\s*bash",
    r"wget.*\|\s*bash",
]

def is_dangerous(cmd):
    for p in DENIED_PATTERNS:
        if re.search(p, cmd, re.IGNORECASE):
            return True
    return False

async def handle(update, context):
    cmd = update.message.text.strip()
    if not cmd:
        return
    if is_dangerous(cmd):
        buf = await take_screenshot()
        await update.message.reply_photo(buf, caption="команда запрещена")
        return
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, executable="/bin/sh", cwd='/')
        out = res.stdout + res.stderr
        if not out:
            out = "(пустой вывод)"
    except subprocess.TimeoutExpired:
        out = "таймаут 10с"
    except Exception as e:
        out = f"ошибка: {e}"
    buf = await take_screenshot()
    caption = f"команда: {cmd}\nвывод:\n{out[:700]}"
    await update.message.reply_photo(buf, caption=caption)

async def take_screenshot():
    try:
        subprocess.run(['scrot', '/tmp/screenshot.png'], check=True, timeout=5)
        with open('/tmp/screenshot.png', 'rb') as f:
            buf = io.BytesIO(f.read())
        buf.seek(0)
        return buf
    except:
        img = Image.new("RGB", (800, 600), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle))
    print("бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
