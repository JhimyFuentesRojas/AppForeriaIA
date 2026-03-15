"""Vistas personalizadas de Flask-Admin con control de acceso por roles"""

from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, flash


class SecureAdminIndexView(AdminIndexView):
    """Vista de índice personalizada para Flask-Admin con restricción de acceso"""

    @expose('/')
    def index(self):
        """Página de inicio del panel de administración"""
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Necesitas permisos de administrador para acceder a esta sección.', 'danger')
            return redirect(url_for('auth.login'))
        return self.render('admin/index.html')


class SecureModelView(ModelView):
    """Vista de Flask-Admin con restricción de acceso solo para administradores"""

    
    list_template = 'admin/model/list.html'
    create_template = 'admin/model/create.html'
    edit_template = 'admin/model/edit.html'
    details_template = 'admin/model/details.html'

    
    can_export = True
    can_view_details = True
    create_modal = False
    edit_modal = False
    can_delete = True
    page_size = 20

    def is_accessible(self):
        """Solo permite acceso a usuarios administradores autenticados"""
        return current_user.is_authenticated and current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        """Redirigir a login si no tiene acceso"""
        flash('Necesitas permisos de administrador para acceder a esta sección.', 'danger')
        return redirect(url_for('auth.login'))
