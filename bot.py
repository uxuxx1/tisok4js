import subprocess
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

TOKEN = "8839915273:AAG-iAMNlAsfY5do3osEOO285kZ9tThBlLc"

async def handle(update: Update, context):
    cmd = update.message.text.strip()
    if not cmd:
        return
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, executable="/bin/sh", cwd='/')
        out = res.stdout + res.stderr
        if not out:
            out = "(пустой вывод)"
    except subprocess.TimeoutExpired:
        out = "таймаут 30с"
    except Exception as e:
        out = f"ошибка: {e}"
    await update.message.reply_text(f"$ {cmd}\n\n{out[:4000]}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle))
    print("бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
