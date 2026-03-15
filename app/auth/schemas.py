"""Schemas de Pydantic para validación de datos de autenticación"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class RegistroSchema(BaseModel):
    """Schema para validar datos de registro de usuario"""
    username: str = Field(..., min_length=3, max_length=80, description="Nombre de usuario")
    email: EmailStr = Field(..., description="Email válido")
    password: str = Field(..., min_length=6, description="Contraseña (mínimo 6 caracteres)")
    password_confirm: str = Field(..., description="Confirmación de contraseña")
    nombre_completo: str = Field(..., min_length=3, max_length=200, description="Nombre completo")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    direccion: Optional[str] = Field(None, description="Dirección")
    rol: str = Field(default='cliente', description="Rol del usuario")

    @field_validator('username')
    @classmethod
    def validar_username(cls, v):
        """Validar que el username solo contenga letras, números y guiones bajos"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('El username solo puede contener letras, números y guiones bajos')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validar_password(cls, v):
        """Validar fortaleza de contraseña"""
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isalpha() for char in v):
            raise ValueError('La contraseña debe contener al menos una letra')
        return v

    @field_validator('password_confirm')
    @classmethod
    def validar_password_confirm(cls, v, info):
        """Validar que las contraseñas coincidan"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

    @field_validator('rol')
    @classmethod
    def validar_rol(cls, v):
        """Validar que el rol sea válido"""
        roles_validos = ['admin', 'vendedor', 'cliente']
        if v not in roles_validos:
            raise ValueError(f'Rol inválido. Debe ser uno de: {", ".join(roles_validos)}')
        return v

    @field_validator('telefono')
    @classmethod
    def validar_telefono(cls, v):
        """Validar formato de teléfono"""
        if v and not re.match(r'^[\d\s\-\+\(\)]+$', v):
            raise ValueError('Formato de teléfono inválido')
        return v


class LoginSchema(BaseModel):
    """Schema para validar datos de login"""
    username: str = Field(..., min_length=3, description="Nombre de usuario o email")
    password: str = Field(..., min_length=6, description="Contraseña")
    remember: bool = Field(default=False, description="Recordar sesión")

    @field_validator('username')
    @classmethod
    def validar_username(cls, v):
        """Normalizar username"""
        return v.strip().lower()


class CambioPasswordSchema(BaseModel):
    """Schema para cambio de contraseña"""
    password_actual: str = Field(..., description="Contraseña actual")
    password_nueva: str = Field(..., min_length=6, description="Nueva contraseña")
    password_nueva_confirm: str = Field(..., description="Confirmación de nueva contraseña")

    @field_validator('password_nueva')
    @classmethod
    def validar_password(cls, v):
        """Validar fortaleza de contraseña"""
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not any(char.isalpha() for char in v):
            raise ValueError('La contraseña debe contener al menos una letra')
        return v

    @field_validator('password_nueva_confirm')
    @classmethod
    def validar_password_confirm(cls, v, info):
        """Validar que las contraseñas coincidan"""
        if 'password_nueva' in info.data and v != info.data['password_nueva']:
            raise ValueError('Las contraseñas no coinciden')
        return v
