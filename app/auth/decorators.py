"""Decoradores para protección de rutas según roles"""

from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def login_required_with_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar si está autenticado
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión para acceder a esta página.', 'warning')
                return redirect(url_for('auth.login'))

            # Verificar si tiene el rol requerido
            if roles and current_user.rol not in roles:
                flash('No tienes permisos para acceder a esta página.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_admin():
            flash('Necesitas permisos de administrador para acceder a esta página.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def vendedor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_vendedor():
            flash('Necesitas permisos de vendedor para acceder a esta página.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function
