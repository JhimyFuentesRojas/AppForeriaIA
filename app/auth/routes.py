"""Rutas del módulo de autenticación"""

from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from pydantic import ValidationError

from app.auth import auth_bp
from app.auth.schemas import RegistroSchema, LoginSchema, CambioPasswordSchema
from app.auth.decorators import cliente_required
from app.models import Usuario
from app.extensions import db


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro de nuevos usuarios"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            datos = RegistroSchema(**request.form.to_dict())
         
            if Usuario.query.filter_by(username=datos.username).first():
                flash('El nombre de usuario ya está registrado.', 'danger')
                return render_template('auth/registro.html')

            if Usuario.query.filter_by(email=datos.email).first():
                flash('El email ya está registrado.', 'danger')
                return render_template('auth/registro.html')

 
            nuevo_usuario = Usuario(
                username=datos.username,
                email=datos.email,
                nombre_completo=datos.nombre_completo,
                telefono=datos.telefono,
                direccion=datos.direccion,
                rol='cliente', 
                activo=True
            )
            nuevo_usuario.set_password(datos.password)

            db.session.add(nuevo_usuario)
            db.session.commit()

            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar usuario: {str(e)}', 'danger')

    return render_template('auth/registro.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuarios"""
    # Si ya está autenticado, redirigir
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            datos = LoginSchema(**request.form.to_dict())

            usuario = Usuario.query.filter(
                (Usuario.username == datos.username) |
                (Usuario.email == datos.username)
            ).first()

            if usuario and usuario.check_password(datos.password):
                if not usuario.activo:
                    flash('Tu cuenta está desactivada. Contacta al administrador.', 'warning')
                    return render_template('auth/login.html')

                usuario.ultima_conexion = datetime.utcnow()
                db.session.commit()

                login_user(usuario, remember=datos.remember)

                flash(f'¡Bienvenido {usuario.nombre_completo}!', 'success')

                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)

                return redirect(url_for('main.index'))
            else:
                flash('Usuario o contraseña incorrectos.', 'danger')

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')

        except Exception as e:
            flash(f'Error al iniciar sesión: {str(e)}', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@cliente_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/perfil')
@cliente_required
def perfil():
    """Ver perfil del usuario"""
    return render_template('auth/perfil.html', usuario=current_user)


@auth_bp.route('/perfil/editar', methods=['GET', 'POST'])
@cliente_required
def editar_perfil():
    """Editar perfil del usuario"""
    if request.method == 'POST':
        try:
            current_user.nombre_completo = request.form.get('nombre_completo', current_user.nombre_completo)
            current_user.telefono = request.form.get('telefono', current_user.telefono)
            current_user.direccion = request.form.get('direccion', current_user.direccion)

            nuevo_email = request.form.get('email')
            if nuevo_email and nuevo_email != current_user.email:
                if Usuario.query.filter_by(email=nuevo_email).first():
                    flash('El email ya está registrado por otro usuario.', 'danger')
                    return render_template('auth/editar_perfil.html', usuario=current_user)
                current_user.email = nuevo_email

            db.session.commit()
            flash('Perfil actualizado exitosamente.', 'success')
            return redirect(url_for('auth.perfil'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')

    return render_template('auth/editar_perfil.html', usuario=current_user)


@auth_bp.route('/perfil/cambiar-password', methods=['GET', 'POST'])
@cliente_required
def cambiar_password():
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        try:
            datos = CambioPasswordSchema(**request.form.to_dict())

            if not current_user.check_password(datos.password_actual):
                flash('La contraseña actual es incorrecta.', 'danger')
                return render_template('auth/cambiar_password.html')

            current_user.set_password(datos.password_nueva)
            db.session.commit()

            flash('Contraseña cambiada exitosamente.', 'success')
            return redirect(url_for('auth.perfil'))

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al cambiar contraseña: {str(e)}', 'danger')

    return render_template('auth/cambiar_password.html')
