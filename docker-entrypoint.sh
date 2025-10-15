#!/bin/bash
set -e

# Log de versiones y configuración
echo "=== Colli Finance API Starting ==="
echo "Python version: $(python --version)"
echo "App version: ${APP_VERSION}"
echo "Environment: ${ENVIRONMENT}"
echo "Log level: ${LOG_LEVEL:-INFO}"
echo "================================"

# Ejecutar el comando pasado como argumentos
exec "$@"