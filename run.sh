#!/bin/bash
# Script de conveniencia para rodar servidor e cliente
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

case "${1:-}" in
    server|servidor)
        echo "Iniciando servidor..."
        cd "$DIR"
        python -m uvicorn servidor.main:app --host 0.0.0.0 --port 4000 --reload
        ;;
    client|cliente)
        echo "Iniciando cliente..."
        cd "$DIR"
        python -m cliente.client
        ;;
    *)
        echo "Uso: ./run.sh [server|client]"
        echo "  server  - Inicia o servidor FastAPI"
        echo "  client  - Inicia o cliente de sincronizacao"
        exit 1
        ;;
esac
