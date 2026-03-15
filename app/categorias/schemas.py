"""Schemas de Pydantic para validación de Categorías"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class CategoriaCreateSchema(BaseModel):
    """Schema para crear una categoría"""
    nombre: str = Field(..., min_length=3, max_length=100, description="Nombre de la categoría")
    descripcion: Optional[str] = Field(None, description="Descripción de la categoría")
    activo: bool = Field(default=True, description="Estado activo/inactivo")

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        """Validar y normalizar nombre"""
        v = v.strip()
        if not v:
            raise ValueError('El nombre no puede estar vacío')
        if len(v) < 3:
            raise ValueError('El nombre debe tener al menos 3 caracteres')
        return v.title()  # Capitalizar cada palabra

    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        """Validar descripción"""
        if v:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('La descripción no puede superar los 500 caracteres')
        return v


class CategoriaUpdateSchema(BaseModel):
    """Schema para actualizar una categoría"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None)
    activo: Optional[bool] = Field(None)

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        """Validar y normalizar nombre"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('El nombre no puede estar vacío')
            if len(v) < 3:
                raise ValueError('El nombre debe tener al menos 3 caracteres')
            return v.title()
        return v

    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        """Validar descripción"""
        if v:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('La descripción no puede superar los 500 caracteres')
        return v


def generar_slug(nombre):
    """Generar slug a partir del nombre"""
    slug = nombre.lower()
    slug = re.sub(r'[áàäâ]', 'a', slug)
    slug = re.sub(r'[éèëê]', 'e', slug)
    slug = re.sub(r'[íìïî]', 'i', slug)
    slug = re.sub(r'[óòöô]', 'o', slug)
    slug = re.sub(r'[úùüû]', 'u', slug)
    slug = re.sub(r'[ñ]', 'n', slug)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    slug = slug.strip('-')
    return slug
