"""Schemas de Pydantic para validación de Productos"""

from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ProductoCreateSchema(BaseModel):
    """Schema para crear un producto"""
    nombre: str = Field(..., min_length=3, max_length=200, description="Nombre del producto")
    descripcion: Optional[str] = Field(None, description="Descripción del producto")
    precio: Decimal = Field(..., gt=0, description="Precio del producto")
    stock: int = Field(default=0, ge=0, description="Stock disponible")
    sku: Optional[str] = Field(None, max_length=50, description="SKU único del producto")
    categoria_id: int = Field(..., gt=0, description="ID de la categoría")
    activo: bool = Field(default=True, description="Estado activo/inactivo")
    destacado: bool = Field(default=False, description="Producto destacado")

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        """Validar y normalizar nombre"""
        v = v.strip()
        if not v:
            raise ValueError('El nombre no puede estar vacío')
        return v.title()

    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        """Validar descripción"""
        if v:
            v = v.strip()
            if len(v) > 1000:
                raise ValueError('La descripción no puede superar los 1000 caracteres')
        return v

    @field_validator('precio')
    @classmethod
    def validar_precio(cls, v):
        """Validar precio"""
        if v <= 0:
            raise ValueError('El precio debe ser mayor a 0')
        if v > 9999999.99:
            raise ValueError('El precio no puede superar $9,999,999.99')
        return round(v, 2)

    @field_validator('stock')
    @classmethod
    def validar_stock(cls, v):
        """Validar stock"""
        if v < 0:
            raise ValueError('El stock no puede ser negativo')
        if v > 999999:
            raise ValueError('El stock no puede superar 999,999 unidades')
        return v

    @field_validator('sku')
    @classmethod
    def validar_sku(cls, v):
        """Validar y normalizar SKU"""
        if v:
            v = v.strip().upper()
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('El SKU solo puede contener letras, números, guiones y guiones bajos')
        return v


class ProductoUpdateSchema(BaseModel):
    """Schema para actualizar un producto"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None)
    precio: Optional[Decimal] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=50)
    categoria_id: Optional[int] = Field(None, gt=0)
    activo: Optional[bool] = Field(None)
    destacado: Optional[bool] = Field(None)

    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        """Validar y normalizar nombre"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('El nombre no puede estar vacío')
            return v.title()
        return v

    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        """Validar descripción"""
        if v:
            v = v.strip()
            if len(v) > 1000:
                raise ValueError('La descripción no puede superar los 1000 caracteres')
        return v

    @field_validator('precio')
    @classmethod
    def validar_precio(cls, v):
        """Validar precio"""
        if v is not None:
            if v <= 0:
                raise ValueError('El precio debe ser mayor a 0')
            if v > 9999999.99:
                raise ValueError('El precio no puede superar $9,999,999.99')
            return round(v, 2)
        return v

    @field_validator('stock')
    @classmethod
    def validar_stock(cls, v):
        """Validar stock"""
        if v is not None:
            if v < 0:
                raise ValueError('El stock no puede ser negativo')
            if v > 999999:
                raise ValueError('El stock no puede superar 999,999 unidades')
        return v

    @field_validator('sku')
    @classmethod
    def validar_sku(cls, v):
        """Validar y normalizar SKU"""
        if v:
            v = v.strip().upper()
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('El SKU solo puede contener letras, números, guiones y guiones bajos')
        return v


class ProductoBusquedaSchema(BaseModel):
    """Schema para búsqueda y filtrado de productos"""
    busqueda: Optional[str] = Field(None, description="Término de búsqueda")
    categoria_id: Optional[int] = Field(None, description="Filtrar por categoría")
    precio_min: Optional[Decimal] = Field(None, ge=0, description="Precio mínimo")
    precio_max: Optional[Decimal] = Field(None, ge=0, description="Precio máximo")
    stock_minimo: Optional[int] = Field(None, ge=0, description="Stock mínimo")
    solo_activos: bool = Field(default=True, description="Solo productos activos")
    solo_destacados: bool = Field(default=False, description="Solo productos destacados")
    orden: str = Field(default='nombre', description="Campo de ordenamiento")

    @field_validator('precio_max')
    @classmethod
    def validar_precio_max(cls, v, info):
        """Validar que precio_max sea mayor que precio_min"""
        if v is not None and 'precio_min' in info.data and info.data['precio_min'] is not None:
            if v < info.data['precio_min']:
                raise ValueError('El precio máximo debe ser mayor al precio mínimo')
        return v
