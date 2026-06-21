FROM python:3.12-alpine
RUN apk add --no-cache xvfb imagemagick jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev harfbuzz-dev fribidi-dev libwebp-dev
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py entrypoint.sh /app/
RUN chmod +x entrypoint.sh
CMD ["/app/entrypoint.sh"]
