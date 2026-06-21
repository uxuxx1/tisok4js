#!/bin/sh
Xvfb :99 -screen 0 1024x768x24 -ac &
export DISPLAY=:99
sleep 3
python3 /app/bot.py
