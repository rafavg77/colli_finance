# TODO List

## Completado
- [x] Integración de catálogo de bancos, `operation_date` obligatorio en transacciones y tablas de listener (alembic revision `0005_banks_listener`) con migraciones automáticas en Docker.
- [x] Exposición de bancos y nuevas reglas en CRUD/routers (tarjetas, transfers, uploads, summary) con datos provenientes de `BANKS_LIST`.
- [x] Limpieza de secretos embebidos: Docker Compose, Makefile y `.env` centralizados para credenciales y configuración.
- [x] Autenticación JWT (`/auth/login`, `/auth/login-phone`, `/auth/register`) con hashing seguro de contraseñas.
- [x] CRUD de usuarios (`/users`) con auditoría para registro, actualización, consulta y eliminación de perfiles.
- [x] Seed automático de categorías al arrancar y CRUD completo de `/categories` con validaciones de duplicados.
- [x] CRUD de tarjetas (`/cards`) con validaciones específicas para crédito, sincronización de banco vía trigger y registros de auditoría.
- [x] CRUD de transacciones (`/transactions`) con auditoría y uso obligatorio de `operation_date`.
- [x] Servicio de transferencias (`/transfers`) con doble movimiento, verificación de saldo y auditoría.
- [x] Gestión de adjuntos y cargas de archivos (`/uploads`) con validaciones de tamaño/tipo y vinculación a transacciones o transferencias.
- [x] Resumen financiero por tarjeta en `/summary/cards` usando agregaciones de `TransactionCRUD.summarize_by_card`.
- [x] Consulta de bitácora de auditoría (`/audit`) soportada por `app/services/audit.py`.
- [x] Configuración de logging estructurado y soporte para Loki en `app/core/logging_config.py`.
- [x] Infraestructura de base de datos asíncrona, creación automática, seeding y pre-limpieza de migraciones (`app/main.py`, `app/tools/pre_migration_cleanup.py`).
- [x] Pruebas automatizadas iniciales para salud, autenticación y transferencias (`tests/test_health.py`, `tests/test_auth.py`, `tests/test_transfers.py`).

## Pendiente
- [ ] Crear el CRUD completo para `banks` (modelos, esquemas, rutas y tests).
- [ ] Crear CRUD para la entidad `listener` (credenciales, plantillas y configuraciones) y exponer endpoints administrativos.
- [ ] Implementar webhook que procese las notificaciones del servicio listener y registre transacciones resultantes.
- [ ] Eliminar todo lo referente a hábitos (`habitos`); moverlo al proyecto correspondiente.
- [ ] Ampliar la cobertura de pruebas automatizadas para módulos críticos (`/cards`, `/categories`, `/transactions`, `/uploads`, `/summary`, `/audit`).
