from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.crud.category import CategoryCRUD
from app.db.models import Category, User
from app.db.session import get_db
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.audit import register_audit

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    categories = await CategoryCRUD.list_all(db)
    return categories


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await CategoryCRUD.get_by_name(db, payload.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La categoría ya existe")
    category = await CategoryCRUD.create(db, name=payload.name)
    await register_audit(
        db,
        user_id=current_user.id,
        action="create",
        resource="category",
        details={"category_id": category.id},
    )
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.get(Category, category_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    category = await CategoryCRUD.update(db, result, name=payload.name)
    await register_audit(
        db,
        user_id=current_user.id,
        action="update",
        resource="category",
        details={"category_id": category.id},
    )
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.get(Category, category_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    await CategoryCRUD.delete(db, result)
    await register_audit(
        db,
        user_id=current_user.id,
        action="delete",
        resource="category",
        details={"category_id": category_id},
    )
    return None
