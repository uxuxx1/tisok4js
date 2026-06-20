FROM alpine:latest
RUN apk add --no-cache python3 py3-pip xvfb
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py entrypoint.sh /app/
WORKDIR /app
RUN chmod +x entrypoint.sh
CMD ["/app/entrypoint.sh"]
