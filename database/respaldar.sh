#!/bin/sh
# Respaldo diario de la base con mysqldump. Guarda los últimos 7 días.
# Uso (desde la raíz del repo, en la VM): sh database/respaldar.sh [carpeta]
# La carpeta por defecto es ~/respaldos.
set -eu

CARPETA="${1:-$HOME/respaldos}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
ARCHIVO="$CARPETA/logistica_$(date +%F).sql.gz"

mkdir -p "$CARPETA"
cd "$RAIZ"

# Se escribe a un temporal para no dejar un respaldo a medias si algo falla.
docker compose exec -T mysql sh -c \
  'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers logistica_policial 2>/dev/null' \
  | gzip > "$ARCHIVO.tmp"

# Un volcado vacío o truncado no tiene la marca final de mysqldump.
if ! gzip -dc "$ARCHIVO.tmp" | tail -n 1 | grep -q "Dump completed"; then
  rm -f "$ARCHIVO.tmp"
  echo "El respaldo no terminó bien" >&2
  exit 1
fi

mv "$ARCHIVO.tmp" "$ARCHIVO"
chmod 600 "$ARCHIVO"

# Conserva solo los 7 más recientes.
ls -1t "$CARPETA"/logistica_*.sql.gz | tail -n +8 | xargs -r rm -f
echo "Respaldo guardado en $ARCHIVO"
