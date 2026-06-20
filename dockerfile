FROM alpine:latest
RUN apk add --no-cache python3 py3-pip xvfb jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev libwebp-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py entrypoint.sh /app/
WORKDIR /app
RUN chmod +x entrypoint.sh
CMD ["/app/entrypoint.sh"]
