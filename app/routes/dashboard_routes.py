"""Rutas para el Dashboard Inteligente"""

from flask import Blueprint, jsonify, render_template, request, send_file
from app.auth.decorators import admin_required
from app.services.analytics_service import AnalyticsService
from app.services.dashboard_pdf_generator import generar_reporte_dashboard_pdf
from app.models import Producto
from app.extensions import db
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard-ia')
@admin_required
def ver_dashboard():
    """Ruta para ver la página del dashboard IA (solo admin)"""
    return render_template('dashboard_ai.html')


@dashboard_bp.route('/api/admin/dashboard-ai', methods=['GET'])
@admin_required
def obtener_datos_dashboard():
    """Endpoint API que proporciona datos para el dashboard IA"""
    try:
        kpis = AnalyticsService.obtener_kpis()
        mas_vendidos = AnalyticsService.obtener_productos_mas_vendidos()
        categorias = AnalyticsService.obtener_categorias_populares()
        alertas_stock = AnalyticsService.obtener_productos_alertas_stock()
        
        resumen_ia = AnalyticsService.generar_resumen_ia()
        
        datos = {
            'kpis': kpis,
            'graficos': {
                'mas_vendidos': mas_vendidos,
                'categorias': categorias
            },
            'alertas_stock': alertas_stock,
            'analisis_ia': resumen_ia
        }
        
        return jsonify(datos)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'analisis_ia': f"Error al generar análisis: {str(e)}"
        }), 500

@dashboard_bp.route('/api/admin/dashboard-report', methods=['GET'])
@admin_required
def descargar_reporte_pdf():
    """Genera y descarga el reporte PDF del Dashboard IA (solo admin)"""
    try:
        kpis = AnalyticsService.obtener_kpis()
        mas_vendidos = AnalyticsService.obtener_productos_mas_vendidos()
        categorias = AnalyticsService.obtener_categorias_populares()
        alertas_stock = AnalyticsService.obtener_productos_alertas_stock()
        analisis = AnalyticsService.generar_analisis_completo_para_reporte()

        buffer = generar_reporte_dashboard_pdf(kpis, mas_vendidos, categorias, alertas_stock, analisis)

        nombre_archivo = f"reporte_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=nombre_archivo,
        )
    except Exception as e:
        return jsonify({'error': f'Error al generar reporte: {str(e)}'}), 500


@dashboard_bp.route('/api/admin/update-stock', methods=['POST'])
@admin_required
def update_stock():
    """Endpoint API para actualizar el stock de un producto"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos JSON'}), 400
            
        producto_id = data.get('producto_id')
        nuevo_stock = data.get('nuevo_stock')
        
        if not producto_id or nuevo_stock is None:
            return jsonify({'success': False, 'message': 'Faltan parámetros requeridos'}), 400
            
        try:
            nuevo_stock = int(nuevo_stock)
            if nuevo_stock < 0:
                return jsonify({'success': False, 'message': 'El stock no puede ser negativo'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'El stock debe ser un número entero'}), 400
            
        producto = Producto.query.get(producto_id)
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404
            
        producto.stock = nuevo_stock
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Stock actualizado exitosamente',
            'producto_id': producto.id,
            'nuevo_stock': producto.stock
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al actualizar stock: {str(e)}'}), 500
