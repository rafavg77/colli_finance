from pydantic import BaseModel, Field


class HabitCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=500)
