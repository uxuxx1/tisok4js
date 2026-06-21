import subprocess
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = "8839915273:AAG-iAMNlAsfY5do3osEOO285kZ9tThBlLc"
OWNER_ID = 297562307

ALLOWED_COMMANDS = {
    'ls', 'pwd', 'whoami', 'date', 'uptime', 'echo', 'cat', 'head', 'tail',
    'grep', 'find', 'tree', 'df', 'du', 'free', 'ps', 'top', 'htop', 'atop',
    'netstat', 'ss', 'ping', 'nslookup', 'dig', 'traceroute', 'tracepath',
    'uname', 'env', 'printenv', 'id', 'groups', 'users', 'w', 'who', 'last',
    'lastlog', 'history', 'which', 'whereis', 'locate', 'cal', 'ncal', 'bc',
    'expr', 'factor', 'seq', 'yes', 'base64', 'md5sum', 'sha1sum', 'sha256sum',
    'wc', 'sort', 'uniq', 'comm', 'diff', 'cmp', 'file', 'stat', 'du'
}

DANGEROUS_COMMANDS = {
    'rm', 'dd', 'mkfs', 'format', 'shutdown', 'reboot', 'halt', 'poweroff',
    'kill', 'pkill', 'killall', 'nice', 'renice', 'chmod', 'chown', 'chroot',
    'mount', 'umount', 'fdisk', 'parted', 'systemctl', 'service', 'apt', 'apt-get',
    'dpkg', 'rpm', 'yum', 'dnf', 'pacman', 'zypper', 'pip', 'npm', 'gem', 'cpan',
    'wget', 'curl', 'scp', 'rsync', 'tar', 'gzip', 'gunzip', 'zip', 'unzip',
    'bzip2', 'xz', '7z', 'rar', 'cp', 'mv', 'ln', 'mkdir', 'rmdir', 'touch',
    'ln', 'link', 'unlink', 'mknod', 'mkfifo', 'tee', 'xargs', 'eval', 'exec'
}

FORBIDDEN_CHARS = {';', '&&', '||', '|', '>', '<', '`', '$', '(', ')', '&', '\n', '!', '{', '}', '[', ']', '*', '?', '~'}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def is_allowed_command(cmd):
    if not cmd:
        return False
    first_word = cmd.split()[0] if cmd.split() else ''
    if first_word not in ALLOWED_COMMANDS:
        return False
    if any(char in cmd for char in FORBIDDEN_CHARS):
        return False
    return True

def is_dangerous(cmd):
    first_word = cmd.split()[0] if cmd.split() else ''
    if first_word in DANGEROUS_COMMANDS:
        return True
    if 'rm -rf' in cmd or 'rm -fr' in cmd or 'dd if' in cmd or 'mkfs' in cmd:
        return True
    return False

async def handle_message(update, context):
    user_id = update.effective_user.id
    cmd = update.message.text.strip()
    if not cmd:
        return

    if not is_owner(user_id):
        if not is_allowed_command(cmd):
            await update.message.reply_text("you have no permission")
            return
        if is_dangerous(cmd):
            await update.message.reply_text("this command is forbidden for you")
            return
    else:
        if is_dangerous(cmd):
            await update.message.reply_text("warning: dangerous command, but executing anyway")

    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30, text=True)
    except subprocess.CalledProcessError as e:
        result = e.output
    except subprocess.TimeoutExpired:
        result = "timeout (30s)"
    except Exception as e:
        result = str(e)

    await send_long_message(update, f"$ {cmd}\n\n{result}")

async def error_handler(update, context):
    logger.error(f"error: {context.error}")
    try:
        await update.message.reply_text("error occurred")
    except:
        pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    logger.info("bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
