#!/bin/bash
set -e

# Log de versiones y configuración
echo "=== Colli Finance API Starting ==="
echo "Python version: $(python --version)"
echo "App version: ${APP_VERSION}"
echo "Environment: ${ENVIRONMENT}"
echo "Log level: ${LOG_LEVEL:-INFO}"
echo "================================"

# Ejecutar migraciones automáticamente antes de iniciar el servicio
if [ "${RUN_MIGRATIONS:-1}" = "1" ] && [ "${DISABLE_STARTUP_MIGRATIONS:-0}" != "1" ]; then
	echo "Ejecutando migraciones de base de datos (make migrate)"
	make migrate
else
	echo "Migraciones automáticas deshabilitadas (RUN_MIGRATIONS=${RUN_MIGRATIONS:-1}, DISABLE_STARTUP_MIGRATIONS=${DISABLE_STARTUP_MIGRATIONS:-0})"
fi

# Ejecutar el comando pasado como argumentos
exec "$@"