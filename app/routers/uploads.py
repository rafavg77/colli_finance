import os
import uuid
from pathlib import Path
from decimal import Decimal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.crud.transaction import TransactionCRUD
from app.crud.attachment import AttachmentCRUD

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _ensure_dir(base: Path):
    base.mkdir(parents=True, exist_ok=True)


def _parse_csv(value: str | None) -> set[str]:
    return set([v.strip().lower() for v in value.split(",") if v.strip()]) if value else set()


def _validate_file_type(file: UploadFile, content: bytes) -> None:
    settings = get_settings()
    allowed_ct = _parse_csv(settings.upload_allowed_content_types) or {"application/pdf"}
    blocked_ct = _parse_csv(settings.upload_blocked_content_types) or {"image/svg+xml"}
    allowed_ext = _parse_csv(settings.upload_allowed_exts) or {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".pdf"}
    blocked_ext = _parse_csv(settings.upload_blocked_exts) or {".svg", ".svgz"}

    ct = (file.content_type or "").lower()
    ext = (Path(file.filename).suffix or "").lower()

    if ct in blocked_ct or ext in blocked_ext:
        raise HTTPException(status_code=415, detail="Tipo de archivo bloqueado.")

    # Permitir images/* no bloqueadas y cualquier CT explícitamente permitido
    if (ct.startswith("image/") and ct not in blocked_ct) or ct in allowed_ct:
        return
    # fallback a extensión si no hay CT permitido
    if ext in allowed_ext and ext not in blocked_ext:
        return
    raise HTTPException(status_code=415, detail="Tipo de archivo no permitido.")


def _validate_file_size(content: bytes) -> None:
    settings = get_settings()
    max_bytes = settings.upload_max_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Archivo demasiado grande. Máximo {settings.upload_max_mb}MB.")


@router.post("/transactions")
async def upload_and_create_transaction(
    file: UploadFile = File(...),
    description: str = Form(...),
    card_id: int = Form(...),
    category_id: int | None = Form(None),
    income: str = Form("0.00"),
    expenses: str = Form("0.00"),
    executed: bool = Form(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    base = Path(settings.upload_dir)
    _ensure_dir(base)

    # Persist file to disk
    ext = Path(file.filename).suffix or ""
    dest_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = base / dest_name
    content = await file.read()
    _validate_file_size(content)
    _validate_file_type(file, content)
    dest_path.write_bytes(content)

    # Create transaction
    tx = await TransactionCRUD.create(
        db,
        user_id=current_user.id,
        card_id=card_id,
        description=description,
        category_id=category_id,
        income=Decimal(income),
        expenses=Decimal(expenses),
        executed=executed,
    )

    # Link attachment
    att = await AttachmentCRUD.create(
        db,
        user_id=current_user.id,
        filename=file.filename,
        path=str(dest_path.relative_to(base)),
        content_type=file.content_type,
        size=len(content),
        transaction_id=tx.id,
        transfer_id=None,
    )

    return {
        "transaction_id": tx.id,
        "attachment_id": att.id,
        "filename": att.filename,
        "stored_as": str(dest_path),
    }


@router.post("/transfers")
async def upload_and_create_transfer(
    file: UploadFile = File(...),
    source_card_id: int = Form(...),
    destination_card_id: int = Form(...),
    amount: str = Form(...),
    description: str | None = Form(None),
    category_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    base = Path(settings.upload_dir)
    _ensure_dir(base)

    # Save file
    ext = Path(file.filename).suffix or ""
    dest_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = base / dest_name
    content = await file.read()
    _validate_file_size(content)
    _validate_file_type(file, content)
    dest_path.write_bytes(content)

    # Create transfer (pair of transactions)
    expense_tx, income_tx = await TransactionCRUD.transfer(
        db,
        user_id=current_user.id,
        source_card_id=source_card_id,
        destination_card_id=destination_card_id,
        amount=Decimal(amount),
        description=description,
        category_id=category_id,
    )

    transfer_id = expense_tx.transfer_id
    att = await AttachmentCRUD.create(
        db,
        user_id=current_user.id,
        filename=file.filename,
        path=str(dest_path.relative_to(base)),
        content_type=file.content_type,
        size=len(content),
        transaction_id=None,
        transfer_id=transfer_id,
    )

    return {
        "transfer_id": transfer_id,
        "source_transaction_id": expense_tx.id,
        "destination_transaction_id": income_tx.id,
        "attachment_id": att.id,
        "filename": att.filename,
        "stored_as": str(dest_path),
    }

@router.get("/transactions/{transaction_id}/attachments")
async def list_attachments_by_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await AttachmentCRUD.list_by_transaction(db, current_user.id, transaction_id)
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "content_type": a.content_type,
            "size": a.size,
            "transaction_id": a.transaction_id,
            "transfer_id": a.transfer_id,
            "path": a.path,
        }
        for a in items
    ]

@router.get("/transfers/{transfer_id}/attachments")
async def list_attachments_by_transfer(
    transfer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = await AttachmentCRUD.list_by_transfer(db, current_user.id, transfer_id)
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "content_type": a.content_type,
            "size": a.size,
            "transaction_id": a.transaction_id,
            "transfer_id": a.transfer_id,
            "path": a.path,
        }
        for a in items
    ]

@router.get("/attachments/{attachment_id}")
async def get_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    a = await AttachmentCRUD.get_by_id(db, current_user.id, attachment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    return {
        "id": a.id,
        "filename": a.filename,
        "content_type": a.content_type,
        "size": a.size,
        "transaction_id": a.transaction_id,
        "transfer_id": a.transfer_id,
        "path": a.path,
    }

@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    inline: bool = Query(False, description="Si true, intenta mostrar en el navegador"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    base = Path(settings.upload_dir)
    a = await AttachmentCRUD.get_by_id(db, current_user.id, attachment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    file_path = base / a.path
    if not file_path.exists():
        raise HTTPException(status_code=410, detail="Archivo no disponible")
    resp = FileResponse(path=str(file_path), filename=a.filename, media_type=a.content_type or "application/octet-stream")
    if inline:
        # Ajustar Content-Disposition a inline; FastAPI pone attachment por defecto con filename
        disp = f"inline; filename*=UTF-8''{a.filename}"
        resp.headers["Content-Disposition"] = disp
    return resp

@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    base = Path(settings.upload_dir)
    a = await AttachmentCRUD.get_by_id(db, current_user.id, attachment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    # try delete file from disk
    try:
        p = base / a.path
        if p.exists():
            p.unlink()
    except Exception:
        # no-op: if file removal fails, still remove DB record
        pass
    await AttachmentCRUD.delete(db, a)
    return {"deleted": True}


@router.get("/attachments")
async def list_attachments(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Simple paginación por usuario
    from sqlalchemy import select
    from app.db.models import Attachment

    res = await db.execute(
        select(Attachment)
        .where(Attachment.user_id == current_user.id)
        .order_by(Attachment.id.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(res.scalars().all())
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "content_type": a.content_type,
            "size": a.size,
            "transaction_id": a.transaction_id,
            "transfer_id": a.transfer_id,
            "path": a.path,
        }
        for a in items
    ]
