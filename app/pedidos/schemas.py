"""Schemas de Pydantic para validación de Pedidos"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class DetallePedidoSchema(BaseModel):
    """Schema para un detalle de pedido"""
    producto_id: int = Field(..., gt=0, description="ID del producto")
    cantidad: int = Field(..., gt=0, description="Cantidad de productos")

    @field_validator('cantidad')
    @classmethod
    def validar_cantidad(cls, v):
        """Validar cantidad"""
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        if v > 1000:
            raise ValueError('La cantidad no puede superar 1000 unidades')
        return v


class PedidoCreateSchema(BaseModel):
    """Schema para crear un pedido"""
    direccion_entrega: str = Field(..., min_length=10, max_length=500, description="Dirección de entrega")
    telefono_contacto: str = Field(..., min_length=7, max_length=20, description="Teléfono de contacto")
    notas: Optional[str] = Field(None, max_length=1000, description="Notas adicionales")
    detalles: List[DetallePedidoSchema] = Field(..., min_length=1, description="Detalles del pedido")

    @field_validator('direccion_entrega')
    @classmethod
    def validar_direccion(cls, v):
        """Validar dirección"""
        v = v.strip()
        if len(v) < 10:
            raise ValueError('La dirección debe tener al menos 10 caracteres')
        return v

    @field_validator('telefono_contacto')
    @classmethod
    def validar_telefono(cls, v):
        """Validar teléfono"""
        v = v.strip()
        if not any(char.isdigit() for char in v):
            raise ValueError('El teléfono debe contener al menos un dígito')
        return v

    @field_validator('detalles')
    @classmethod
    def validar_detalles(cls, v):
        """Validar que haya al menos un producto"""
        if not v:
            raise ValueError('El pedido debe tener al menos un producto')
        # productos_ids = [d.producto_id for d in v]
        if len(productos_ids) != len(set(productos_ids)):
            raise ValueError('No puede haber productos duplicados en el pedido')
        return v


class PedidoUpdateSchema(BaseModel):
    """Schema para actualizar un pedido"""
    estado: Optional[str] = Field(None, description="Estado del pedido")
    direccion_entrega: Optional[str] = Field(None, min_length=10, max_length=500)
    telefono_contacto: Optional[str] = Field(None, min_length=7, max_length=20)
    notas: Optional[str] = Field(None, max_length=1000)
    fecha_entrega: Optional[datetime] = Field(None, description="Fecha de entrega")

    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        """Validar que el estado sea válido"""
        if v is not None:
            estados_validos = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado']
            if v not in estados_validos:
                raise ValueError(f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}')
        return v

    @field_validator('direccion_entrega')
    @classmethod
    def validar_direccion(cls, v):
        """Validar dirección"""
        if v is not None:
            v = v.strip()
            if len(v) < 10:
                raise ValueError('La dirección debe tener al menos 10 caracteres')
        return v

    @field_validator('telefono_contacto')
    @classmethod
    def validar_telefono(cls, v):
        """Validar teléfono"""
        if v is not None:
            v = v.strip()
            if not any(char.isdigit() for char in v):
                raise ValueError('El teléfono debe contener al menos un dígito')
        return v


def generar_numero_pedido():
    """Generar número único de pedido"""
    import random
    import string
    from datetime import datetime

    fecha = datetime.now().strftime('%Y%m%d')
    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PED-{fecha}-{codigo}"
