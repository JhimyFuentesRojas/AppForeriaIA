"""
Generador de Facturas en PDF para pedidos
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime


def generar_factura_pdf(pedido):
    """
    Genera un PDF de factura para un pedido

    Args:
        pedido: Objeto Pedido con sus detalles y cliente

    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = BytesIO()

    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elementos = []

    # Estilos
    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'CustomTitle',
        parent=estilos['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#198754'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    estilo_normal = estilos['Normal']
    estilo_bold = ParagraphStyle(
        'Bold',
        parent=estilos['Normal'],
        fontName='Helvetica-Bold'
    )

    # Título
    elementos.append(Paragraph("FACTURA DE VENTA", estilo_titulo))
    elementos.append(Spacer(1, 0.2*inch))

    # Información de la empresa
    datos_empresa = [
        [Paragraph("<b>Florería Examen</b>", estilo_normal)],
        [Paragraph("Dirección: Calle Principal #123", estilo_normal)],
        [Paragraph("Teléfono: (555) 123-4567", estilo_normal)],
        [Paragraph("Email: info@floreria.com", estilo_normal)]
    ]

    tabla_empresa = Table(datos_empresa, colWidths=[6*inch])
    tabla_empresa.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_empresa)
    elementos.append(Spacer(1, 0.3*inch))

    # Separador
    elementos.append(Spacer(1, 0.1*inch))

    # Información del pedido y cliente
    info_pedido = [
        [Paragraph("<b>Número de Pedido:</b>", estilo_normal),
         Paragraph(pedido.numero_pedido, estilo_normal)],
        [Paragraph("<b>Fecha:</b>", estilo_normal),
         Paragraph(pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M'), estilo_normal)],
        [Paragraph("<b>Cliente:</b>", estilo_normal),
         Paragraph(pedido.cliente.nombre_completo, estilo_normal)],
        [Paragraph("<b>Email:</b>", estilo_normal),
         Paragraph(pedido.cliente.email, estilo_normal)],
        [Paragraph("<b>Teléfono:</b>", estilo_normal),
         Paragraph(pedido.telefono_contacto or pedido.cliente.telefono or "N/A", estilo_normal)],
        [Paragraph("<b>Dirección de entrega:</b>", estilo_normal),
         Paragraph(pedido.direccion_entrega, estilo_normal)]
    ]

    tabla_info = Table(info_pedido, colWidths=[2*inch, 4*inch])
    tabla_info.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
    ]))
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 0.4*inch))

    # Título de productos
    elementos.append(Paragraph("<b>Detalle de Productos</b>", estilo_bold))
    elementos.append(Spacer(1, 0.1*inch))

    # Tabla de productos
    datos_productos = [[
        Paragraph("<b>Producto</b>", estilo_normal),
        Paragraph("<b>Cantidad</b>", estilo_normal),
        Paragraph("<b>Precio Unit.</b>", estilo_normal),
        Paragraph("<b>Subtotal</b>", estilo_normal)
    ]]

    for detalle in pedido.detalles:
        datos_productos.append([
            Paragraph(detalle.producto.nombre, estilo_normal),
            Paragraph(str(detalle.cantidad), estilo_normal),
            Paragraph(f"${float(detalle.precio_unitario):,.2f}", estilo_normal),
            Paragraph(f"${float(detalle.subtotal):,.2f}", estilo_normal)
        ])

    # Fila vacía antes del total
    datos_productos.append([
        Paragraph("", estilo_normal),
        Paragraph("", estilo_normal),
        Paragraph("", estilo_normal),
        Paragraph("", estilo_normal)
    ])

    # Agregar línea de total
    datos_productos.append([
        Paragraph("", estilo_normal),
        Paragraph("", estilo_normal),
        Paragraph("<b>TOTAL:</b>", estilo_bold),
        Paragraph(f"<b>${float(pedido.total):,.2f}</b>", estilo_bold)
    ])

    tabla_productos = Table(datos_productos, colWidths=[2.8*inch, 1*inch, 1.3*inch, 1.3*inch])
    tabla_productos.setStyle(TableStyle([
        # Encabezados
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),

        # Cuerpo de la tabla
        ('ALIGN', (1, 1), (1, -3), 'CENTER'),
        ('ALIGN', (2, 1), (2, -3), 'RIGHT'),
        ('ALIGN', (3, 1), (3, -3), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -3), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -3), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -3), 8),
        ('TOPPADDING', (0, 1), (-1, -3), 8),
        ('GRID', (0, 0), (-1, -3), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.white, colors.HexColor('#f8f9fa')]),

        # Fila vacía antes del total (sin borde)
        ('LINEBELOW', (0, -2), (-1, -2), 0, colors.white),
        ('LINEABOVE', (0, -2), (-1, -2), 0, colors.white),

        # Fila de total
        ('ALIGN', (2, -1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, -1), (-1, -1), 13),
        ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#198754')),
        ('TEXTCOLOR', (2, -1), (-1, -1), colors.white),
        ('BOTTOMPADDING', (2, -1), (-1, -1), 12),
        ('TOPPADDING', (2, -1), (-1, -1), 12),
        ('BOX', (2, -1), (-1, -1), 2, colors.HexColor('#198754')),
    ]))
    elementos.append(tabla_productos)
    elementos.append(Spacer(1, 0.4*inch))

    # Notas si existen
    if pedido.notas:
        elementos.append(Paragraph("<b>Notas:</b>", estilo_bold))
        elementos.append(Spacer(1, 0.05*inch))
        elementos.append(Paragraph(pedido.notas, estilo_normal))
        elementos.append(Spacer(1, 0.3*inch))

    # Pie de página
    elementos.append(Spacer(1, 0.5*inch))
    estilo_footer = ParagraphStyle(
        'Footer',
        parent=estilos['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elementos.append(Paragraph("<i>¡Gracias por su compra!</i>", estilo_footer))
    elementos.append(Paragraph("Florería - Tu florería de confianza", estilo_footer))

    # Construir PDF
    doc.build(elementos)

    # Mover el puntero al inicio del buffer
    buffer.seek(0)

    return buffer
