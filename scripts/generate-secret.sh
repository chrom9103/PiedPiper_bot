#!/bin/bash
# .env から POSTGRES_PASSWORD を読み取り、K8s Secret マニフェストを生成する
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env"
OUTPUT_FILE="${PROJECT_ROOT}/k8s/postgres-secret.yaml"

DB_USER="digitart-bot"
DB_NAME="digitart-bot"
DB_HOST="postgres"
DB_PORT="5432"

# .env からパスワードを読み取る
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: .env file not found at $ENV_FILE" >&2
    exit 1
fi

POSTGRES_PASSWORD=$(grep -E '^POSTGRES_PASSWORD=' "$ENV_FILE" | sed 's/^POSTGRES_PASSWORD=//' | tr -d '"')

if [[ -z "$POSTGRES_PASSWORD" || "$POSTGRES_PASSWORD" == "CHANGE_ME" ]]; then
    echo "ERROR: POSTGRES_PASSWORD is not set or still default in .env" >&2
    exit 1
fi

DATABASE_URL="postgresql://${DB_USER}:${POSTGRES_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

cat > "$OUTPUT_FILE" <<EOF
# 直接編集せず、.env の POSTGRES_PASSWORD を変更してスクリプトを再実行してください
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  password: "${POSTGRES_PASSWORD}"
  database-url: "${DATABASE_URL}"
EOF

echo "Generated $OUTPUT_FILE"
