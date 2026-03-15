"""Utilidades para manejo de imágenes de productos (RETO ADICIONAL)"""

import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image


def extension_permitida(filename):
    """Verificar si la extensión del archivo está permitida"""
    if '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ALLOWED_EXTENSIONS']


def generar_nombre_unico(filename):
    """Generar un nombre único para el archivo"""
    extension = filename.rsplit('.', 1)[1].lower()
    nombre_unico = f"{uuid.uuid4().hex}.{extension}"
    return nombre_unico


def guardar_imagen(archivo, carpeta='uploads'):
    """
    Guardar imagen con validaciones y optimización

    Args:
        archivo: Archivo de imagen (FileStorage)
        carpeta: Subcarpeta donde guardar (default: 'uploads')

    Returns:
        str: Nombre del archivo guardado o None si hay error
    """
    if not archivo:
        return None

    if archivo.filename == '':
        return None

    if not extension_permitida(archivo.filename):
        raise ValueError(f'Extensión de archivo no permitida. Extensiones permitidas: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}')

    try:
        filename = secure_filename(archivo.filename)
        nombre_unico = generar_nombre_unico(filename)

        upload_folder = Path(current_app.config['UPLOAD_FOLDER']) / carpeta
        upload_folder.mkdir(parents=True, exist_ok=True)

        filepath = upload_folder / nombre_unico

        archivo.save(str(filepath))

        optimizar_imagen(filepath)

        return f"uploads/{carpeta}/{nombre_unico}"

    except Exception as e:
        raise Exception(f'Error al guardar imagen: {str(e)}')


def optimizar_imagen(filepath, max_size=(1200, 1200), quality=85):
    """
    Optimizar imagen: redimensionar y comprimir

    Args:
        filepath: Ruta del archivo
        max_size: Tamaño máximo (ancho, alto) en píxeles
        quality: Calidad de compresión (1-100)
    """
    try:
        with Image.open(filepath) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            img.save(filepath, 'JPEG', quality=quality, optimize=True)

    except Exception as e:
        raise Exception(f'Error al optimizar imagen: {str(e)}')


def eliminar_imagen(ruta_imagen):
    """
    Eliminar archivo de imagen del servidor

    Args:
        ruta_imagen: Ruta relativa de la imagen desde static/ (ej: 'uploads/productos/abc123.jpg')

    Returns:
        bool: True si se eliminó exitosamente, False si no existe
    """
    if not ruta_imagen:
        return False

    try:
        ruta_relativa = ruta_imagen.replace('uploads/', '', 1) if ruta_imagen.startswith('uploads/') else ruta_imagen
        filepath = Path(current_app.config['UPLOAD_FOLDER']) / ruta_relativa
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    except Exception:
        return False


def validar_tamano_archivo(archivo, max_mb=16):
    """
    Validar que el archivo no supere el tamaño máximo

    Args:
        archivo: Archivo (FileStorage)
        max_mb: Tamaño máximo en MB

    Returns:
        bool: True si es válido, False si supera el tamaño
    """
    if not archivo:
        return False

    archivo.seek(0, os.SEEK_END)
    size = archivo.tell()
    archivo.seek(0)  
    max_bytes = max_mb * 1024 * 1024
    return size <= max_bytes


def generar_sku_unico():
    """Generar SKU único para producto"""
    import random
    import string

    codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"FLO-{codigo}"
