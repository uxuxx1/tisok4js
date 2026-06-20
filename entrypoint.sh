#!/bin/sh
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
sleep 2
python3 /app/bot.py
