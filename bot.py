import subprocess
import asyncio
import logging
import os
import pty
import select
import threading
import time
import shlex
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8839915273:AAG-iAMNlAsfY5do3osEOO285kZ9tThBlLc"
OWNER_ID = 297562307

BASE_DIR = "/app/data"
os.makedirs(BASE_DIR, exist_ok=True)

sessions = {}
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerminalSession:
    def __init__(self, user_id):
        self.user_dir = os.path.join(BASE_DIR, str(user_id))
        os.makedirs(self.user_dir, exist_ok=True)
        self.cwd = self.user_dir
        self.master_fd, self.slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            text=True,
            bufsize=0,
            cwd=self.cwd
        )
        self.output_buffer = ""
        self.running = True
        self.last_activity = time.time()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while self.running:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 1024).decode('utf-8', errors='ignore')
                    if data:
                        self.output_buffer += data
                        self.last_activity = time.time()
            except:
                break

    def execute(self, command):
        if not self.running:
            return "session closed"
        # обновляем cwd при cd
        if command.strip().startswith("cd "):
            parts = shlex.split(command)
            if len(parts) == 2:
                new_path = parts[1]
                if os.path.isabs(new_path):
                    self.cwd = os.path.normpath(new_path)
                else:
                    self.cwd = os.path.normpath(os.path.join(self.cwd, new_path))
                if not os.path.exists(self.cwd):
                    self.cwd = self.user_dir
        os.write(self.master_fd, (command + "\n").encode())
        time.sleep(0.3)
        for _ in range(10):
            time.sleep(0.1)
            if self.output_buffer:
                break
        out = self.output_buffer
        self.output_buffer = ""
        self.last_activity = time.time()
        return out

    def getcwd(self):
        return self.cwd

    def close(self):
        self.running = False
        os.close(self.master_fd)
        os.close(self.slave_fd)
        self.process.terminate()

def is_owner(user_id):
    return user_id == OWNER_ID

async def send_long_message(update, text, max_len=4096):
    if not text:
        await update.message.reply_text("(empty output)")
        return
    if len(text) <= max_len:
        await update.message.reply_text(text)
    else:
        parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
        for part in parts:
            await update.message.reply_text(part)
            await asyncio.sleep(0.1)

async def handle_message(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    if not text:
        return
    cmd = text.strip()

    if cmd == "screenshottt":
        if not is_owner(user_id):
            await update.message.reply_text("no permission")
            return
        await take_screenshot(update)
        return

    if cmd.startswith("sendfile "):
        if not is_owner(user_id):
            await update.message.reply_text("no permission")
            return
        args = shlex.split(cmd)
        if len(args) < 2:
            await update.message.reply_text("usage: sendfile <path>")
            return
        file_path = args[1]
        if not os.path.isabs(file_path):
            session = sessions.get(user_id)
            if session:
                file_path = os.path.normpath(os.path.join(session.getcwd(), file_path))
        if not os.path.exists(file_path):
            await update.message.reply_text("file not found")
            return
        if os.path.isdir(file_path):
            await update.message.reply_text("is a directory")
            return
        try:
            with open(file_path, "rb") as f:
                await update.message.reply_document(document=f, filename=os.path.basename(file_path))
        except Exception as e:
            await update.message.reply_text(f"error: {e}")
        return

    # терминал
    if user_id not in sessions:
        sessions[user_id] = TerminalSession(user_id)
        await update.message.reply_text(f"term started (cwd: {sessions[user_id].getcwd()})")

    session = sessions[user_id]

    if cmd == "exit":
        session.close()
        del sessions[user_id]
        await update.message.reply_text("term closed")
        return

    if cmd == "ls":
        cmd = "ls /"

    try:
        result = session.execute(cmd)
        if not result.strip():
            result = "(no output)"
        await send_long_message(update, f"$ {cmd}\n\n{result}")
    except Exception as e:
        await update.message.reply_text(f"error: {e}")

async def handle_document(update, context):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("no permission")
        return
    doc = update.message.document
    if not doc:
        return
    if user_id not in sessions:
        sessions[user_id] = TerminalSession(user_id)
    session = sessions[user_id]
    save_dir = session.getcwd()
    file_path = os.path.join(save_dir, doc.file_name)
    try:
        file = await doc.get_file()
        await file.download_to_drive(file_path)
        await update.message.reply_text(f"file saved: {file_path}")
    except Exception as e:
        await update.message.reply_text(f"error: {e}")

async def take_screenshot(update):
    try:
        subprocess.check_call(["which", "scrot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        await update.message.reply_text("installing scrot...")
        subprocess.check_call(["apt", "update", "-qq"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.check_call(["apt", "install", "-y", "-qq", "scrot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp_file = "/tmp/screenshot.png"
    try:
        subprocess.check_call(["scrot", tmp_file], timeout=10)
        with open(tmp_file, "rb") as f:
            await update.message.reply_photo(photo=f)
        os.unlink(tmp_file)
    except Exception as e:
        await update.message.reply_text(f"screenshot error: {e}")

async def error_handler(update, context):
    logger.error(f"error: {context.error}")
    try:
        await update.message.reply_text("error occurred")
    except:
        pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)
    logger.info("bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
