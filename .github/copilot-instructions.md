# Copilot Instructions for Colli Finance API

## Project Overview

Colli Finance is a personal finance management REST API built with FastAPI, SQLAlchemy 2.0, and PostgreSQL. The application provides comprehensive financial management with JWT authentication, action auditing, structured logging, and support for multiple banks and cards.

## Tech Stack

### Core Technologies
- **FastAPI 0.110.0**: Modern, high-performance web framework
- **Python 3.11+**: Programming language with type hints
- **SQLAlchemy 2.0.25**: Async ORM for database operations
- **PostgreSQL 13+**: Relational database
- **Pydantic 2.6.4**: Data validation and settings management
- **Alembic 1.13.1**: Database migration management

### Key Libraries
- **asyncpg**: Async PostgreSQL driver
- **python-jose**: JWT token management
- **passlib + bcrypt**: Secure password hashing
- **python-json-logger**: Structured JSON logging
- **pytest + pytest-asyncio**: Testing framework

## Project Structure

```
app/
├── core/           # Configuration, security, dependencies, logging
├── crud/           # Database CRUD operations (async)
├── db/             # SQLAlchemy models and session management
│   ├── models/     # Database models (User, Card, Transaction, etc.)
│   ├── base.py     # Base class for models
│   └── session.py  # Async session configuration
├── routers/        # FastAPI endpoints/routes
├── schemas/        # Pydantic models for request/response validation
├── services/       # Business logic (audit, transfers, etc.)
└── main.py         # Application entry point

alembic/            # Database migrations
tests/              # Automated tests (pytest)
```

## Coding Conventions

### Python Style
- **Follow PEP 8** style guidelines
- **Use type hints** for all function parameters and return values
- **Prefer async/await** for all I/O operations
- **Use descriptive variable names** in English
- **Add docstrings** only when logic is complex or non-obvious

### Async Patterns
- **Always use async** for database operations
- **Use `AsyncSession`** for SQLAlchemy database sessions
- **Use `async def`** for route handlers and CRUD methods
- **Use `await`** for all async operations

Example:
```python
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    transaction = await TransactionCRUD.get_by_id(db, transaction_id, current_user.id)
    return transaction
```

### Database Operations
- **Use CRUD classes** for database operations (located in `app/crud/`)
- **Never use raw SQL** unless absolutely necessary
- **Use SQLAlchemy 2.0 syntax** with `select()`, `insert()`, `update()`, `delete()`
- **Always filter by user_id** for user-scoped resources
- **Use transactions** for operations that modify multiple records

Example CRUD pattern:
```python
class TransactionCRUD:
    @staticmethod
    async def get_by_id(db: AsyncSession, transaction_id: int, user_id: int) -> Transaction | None:
        result = await db.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
```

### Pydantic Schemas
- **Use Pydantic models** for all request/response data
- **Separate schemas** for Create, Update, and Response operations
- **Use `ConfigDict`** for model configuration
- **Validate data types** and constraints

Example schema pattern:
```python
class TransactionCreate(BaseModel):
    card_id: int
    description: str
    income: Decimal = Decimal("0.00")
    expenses: Decimal = Decimal("0.00")
    operation_date: date
    category_id: int | None = None
    executed: bool = True

class TransactionResponse(BaseModel):
    id: int
    card_id: int
    description: str
    income: Decimal
    expenses: Decimal
    operation_date: date
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

### Router Patterns
- **Use APIRouter** with prefix and tags
- **Use dependency injection** for database sessions and authentication
- **Return appropriate HTTP status codes** (201 for creation, 404 for not found, etc.)
- **Raise HTTPException** for errors with proper status codes
- **Register audit events** for critical operations

Example router:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.card import CardCRUD
from app.crud.transaction import TransactionCRUD
from app.db.models import User
from app.db.session import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.audit import register_audit

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate ownership
    card = await CardCRUD.get_by_id(db, payload.card_id, current_user.id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Create transaction
    transaction = await TransactionCRUD.create(db, current_user.id, **payload.model_dump())
    
    # Register audit
    await register_audit(db, current_user.id, "transaction_created", transaction.id)
    
    return transaction
```

## Authentication & Security

- **Use JWT tokens** for authentication (`python-jose`)
- **Hash passwords** with bcrypt (`passlib[bcrypt]`)
- **Never store plain-text passwords**
- **Use `get_current_user` dependency** to protect routes
- **Validate user ownership** of resources before operations
- **Use OAuth2PasswordBearer** for token handling

## Logging

- **Use structured logging** with JSON format via custom configuration in `app/core/logging_config.py`
- **Use `get_logger(__name__)`** to get module-specific loggers (configured with `python-json-logger`)
- **Log important events** with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- **Include context** in log messages using the `extra` parameter with a nested structure: `extra={"details": {"event": "event_name", "extra": {...}}}`
- **Log at INFO level** for business operations
- **Log at DEBUG level** for detailed debugging information
- Logs can be sent to **Grafana Loki** if configured via `LOKI_URL` environment variable

Logging structure:
```python
extra={
    "details": {
        "event": "event_name",           # Event identifier
        "extra": {                        # Additional context data
            "key": "value",
            ...
        }
    }
}
```

Example:
```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

logger.info(
    "Transaction created",
    extra={
        "details": {
            "event": "transaction_created",
            "extra": {"transaction_id": transaction.id, "user_id": user_id}
        }
    }
)
```

## Auditing

- **Register audit events** for all critical operations using `app/services/audit.py`
- **Audit operations**: create, update, delete for users, cards, transactions, transfers
- **Include resource details** in audit events
- **Use consistent event names**: `transaction_created`, `card_updated`, `transfer_executed`, etc.

Example:
```python
from app.services.audit import register_audit

await register_audit(
    db=db,
    user_id=current_user.id,
    action="transaction_created",
    resource_id=transaction.id,
    resource_type="transaction",
    details={"card_id": transaction.card_id, "amount": float(transaction.expenses)}
)
```

## Database Migrations

- **Use Alembic** for database schema changes
- **Run `alembic revision --autogenerate -m "description"`** to create migrations
- **Review auto-generated migrations** before applying
- **Test migrations** in development before production
- **Migrations run automatically** on startup if `MIGRATE_ON_START=true`

## Testing

- **Use pytest** with async support (`pytest-asyncio`)
- **Write async tests** for async code
- **Use fixtures** for common test setup (see `tests/conftest.py`)
- **Test CRUD operations**, route handlers, and business logic
- **Use `httpx.AsyncClient`** for API testing
- **Mock external dependencies** when appropriate

Example test:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_transaction(client: AsyncClient, test_user, auth_headers):
    response = await client.post(
        "/transactions",
        json={
            "card_id": 1,
            "description": "Test transaction",
            "expenses": "100.00",
            "operation_date": "2024-01-01"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["description"] == "Test transaction"
```

### Test Configuration
- Tests use `asyncio_mode = auto` (configured in `pytest.ini`)
- Use `make test` to run tests
- Use `make test-docker` for Docker-based testing

## File Uploads

- **Use `python-multipart`** for file uploads
- **Validate file types and sizes** before processing
- **Store files** in the `UPLOAD_DIR` directory
- **Block potentially dangerous files** (SVG by default)
- **Support common formats**: PNG, JPG, PDF
- **Link attachments** to transactions via the Attachment model

## Environment Configuration

- **Use pydantic-settings** for configuration management
- **Load settings** from `.env` file
- **Access settings** via `get_settings()` singleton
- **Never hardcode** secrets or configuration values
- **Use environment variables** for all configurable values

## Domain-Specific Rules

### Cards
- Cards belong to users (`user_id`)
- Cards are linked to banks (`bank_id`)
- Support both debit and credit cards (`card_type`)
- Credit cards have `credit_limit` and `available_balance`
- Debit cards only track `available_balance`

### Transactions
- **Always require `operation_date`** (mandatory field)
- Transactions must have either `income` or `expenses` (or both)
- Transactions belong to cards which belong to users
- Transactions can have optional categories
- Transactions can have file attachments
- Track if transaction is `executed` (completed) or pending

### Transfers
- Transfers are between cards of the same user
- Create two transactions: one debit (source) and one credit (destination)
- Validate sufficient balance before transfer
- Link source and destination transactions
- Support optional attachments

### Categories
- Pre-seeded categories: Despensa, Salud, Diversión, Alimentos, Educación, Transporte, Servicios
- Categories are user-specific
- Prevent duplicate category names per user

## Error Handling

- **Use HTTPException** for client errors (400-499)
- **Include descriptive error messages**
- **Use appropriate status codes**:
  - 400: Bad Request (validation errors)
  - 401: Unauthorized (authentication required)
  - 403: Forbidden (insufficient permissions)
  - 404: Not Found (resource doesn't exist)
  - 409: Conflict (duplicate resources)
  - 422: Unprocessable Entity (Pydantic validation errors)
  - 500: Internal Server Error (unexpected errors)

## Common Commands

```bash
# Run the application
uvicorn app.main:app --reload

# Run tests
make test
pytest

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## What NOT to Do

- ❌ Don't use synchronous database operations
- ❌ Don't bypass authentication on protected routes
- ❌ Don't skip user ownership validation
- ❌ Don't hardcode configuration values
- ❌ Don't use raw SQL queries without justification
- ❌ Don't forget to register audit events for critical operations
- ❌ Don't store sensitive data in logs
- ❌ Don't modify database schema without migrations
- ❌ Don't expose internal errors to clients

## Best Practices

- ✅ Always validate user ownership of resources
- ✅ Use type hints for better code clarity
- ✅ Write descriptive commit messages
- ✅ Keep functions focused and small
- ✅ Use dependency injection for testability
- ✅ Log important business events
- ✅ Handle errors gracefully
- ✅ Write tests for new features
- ✅ Keep related code together (routers with business logic)
- ✅ Use Pydantic for data validation
- ✅ Follow the existing code patterns

## Language

- **Code comments**: Spanish (when needed, but prefer self-documenting code)
- **Variable names**: English
- **API documentation**: Spanish
- **Error messages**: Spanish for user-facing messages
- **Logs**: English for event names, Spanish for descriptions when appropriate
