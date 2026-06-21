#!/bin/sh
# установка базовых пакетов
apt update -qq && apt install -y -qq \
    curl wget git net-tools htop vim nano \
    python3-pip python3-dev build-essential \
    && pip3 install --upgrade pip -q
# запуск бота
python3 /app/bot.py
