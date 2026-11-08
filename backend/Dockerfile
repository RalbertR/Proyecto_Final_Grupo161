FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
RUN mkdir -p /app/archivos_privados/documentos \
    && chown nobody:nogroup /app/archivos_privados/documentos \
    && chmod 700 /app/archivos_privados/documentos
USER nobody
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
