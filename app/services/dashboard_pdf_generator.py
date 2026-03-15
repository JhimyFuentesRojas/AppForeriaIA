from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable, KeepTogether,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable
from io import BytesIO
from datetime import datetime

# ── Constantes de layout ───────────────────────────────────────────────────────
PAGE_W   = 7.2 * inch   
COL2_L   = 3.45 * inch  
COL2_R   = 3.65 * inch
COL2_GAP = 0.1  * inch

# ── Paleta ─────────────────────────────────────────────────────────────────────
C_DARK    = colors.HexColor('#0a1628')
C_BLUE    = colors.HexColor('#0d6efd')
C_BLUE_L  = colors.HexColor('#dce8fd')
C_GREEN   = colors.HexColor('#198754')
C_GREEN_L = colors.HexColor('#d8f0e4')
C_PURPLE  = colors.HexColor('#6f42c1')
C_PURP_L  = colors.HexColor('#ede9fb')
C_RED     = colors.HexColor('#dc3545')
C_RED_L   = colors.HexColor('#fbe8ea')
C_ORANGE  = colors.HexColor('#f59e0b')
C_ORANGE_L= colors.HexColor('#fef3cd')
C_GREY    = colors.HexColor('#6c757d')
C_GREY_L  = colors.HexColor('#f8f9fa')
C_DARK_T  = colors.HexColor('#212529')
WHITE     = colors.white


# ── Helpers de estilo ──────────────────────────────────────────────────────────
_style_cache = {}

def S(name, **kw):
    """Crea o reutiliza un ParagraphStyle."""
    key = (name, tuple(sorted(kw.items())))
    if key not in _style_cache:
        base = getSampleStyleSheet()['Normal']
        _style_cache[key] = ParagraphStyle(f's_{len(_style_cache)}', parent=base, **kw)
    return _style_cache[key]


# ── Flowable personalizado: rectángulo de porcentaje ──────────────────────────
class BarraProgreso(Flowable):
    """Barra de progreso dibujada, sin caracteres Unicode."""
    def __init__(self, porcentaje, color, width=2.8*inch, height=10):
        super().__init__()
        self.pct    = min(max(porcentaje, 0), 100)
        self.color  = color
        self.width  = width
        self.height = height

    def draw(self):
        # fondo gris
        self.canv.setFillColor(colors.HexColor('#e9ecef'))
        self.canv.rect(0, 1, self.width, self.height - 2, fill=1, stroke=0)
        # relleno de color
        fill_w = self.width * (float(self.pct) / 100)
        if fill_w > 0:
            self.canv.setFillColor(self.color)
            self.canv.rect(0, 1, fill_w, self.height - 2, fill=1, stroke=0)


# ── Encabezado ─────────────────────────────────────────────────────────────────
def _header(fecha_str):
    out = []

    t = Table([[
        Paragraph('REPORTE EJECUTIVO  |  DASHBOARD IA',
                  S('hb', fontSize=8, fontName='Helvetica-Bold',
                    textColor=WHITE, alignment=TA_LEFT)),
        Paragraph(f'Generado: {fecha_str}',
                  S('hd', fontSize=7.5, textColor=colors.HexColor('#adb5bd'),
                    alignment=TA_RIGHT, fontName='Helvetica')),
    ]], colWidths=[PAGE_W * 0.55, PAGE_W * 0.45])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_DARK),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    out.append(t)
    out.append(Spacer(1, 0.18*inch))

    # Nombre empresa + subtítulo
    out.append(Paragraph('Floreria Crescendo',
               S('et', fontSize=24, fontName='Helvetica-Bold',
                 textColor=C_DARK, spaceAfter=2)))
    out.append(Spacer(3, 0.2*inch))
    # Línea doble de acento
    out.append(HRFlowable(width='100%', thickness=3, color=C_BLUE, spaceAfter=2))
    out.append(HRFlowable(width='100%', thickness=1, color=C_PURPLE, spaceAfter=0))
    out.append(Spacer(1, 0.2*inch))
    return out


# ── KPIs ───────────────────────────────────────────────────────────────────────
def _kpis(kpis):
    datos = [
        ('Ventas Totales',    f"${kpis['ventas_totales']:,.2f}", C_BLUE,   C_BLUE_L),
        ('Pedidos Hoy',       str(kpis['pedidos_hoy']),          C_GREEN,  C_GREEN_L),
        ('Total Productos',   str(kpis['total_productos']),       C_PURPLE, C_PURP_L),
        ('Alertas de Stock',  str(kpis['productos_bajo_stock']), C_RED,    C_RED_L),
    ]
    celdas = []
    for etiqueta, valor, color, bg in datos:
        celda = Table(
            [[Paragraph(valor,   S(f'kv{etiqueta}', fontSize=18, fontName='Helvetica-Bold',
                                   textColor=color, alignment=TA_CENTER))],
             [Paragraph(etiqueta, S(f'kl{etiqueta}', fontSize=8,  fontName='Helvetica',
                                    textColor=C_GREY, alignment=TA_CENTER))]],
            colWidths=[1.7*inch],
        )
        celda.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), bg),
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 10),
            ('BOTTOMPADDING', (0,0),(-1,-1), 10),
            ('LINEBELOW',     (0,-1),(-1,-1), 3, color),
        ]))
        celdas.append(celda)

    cont = Table([celdas], colWidths=[1.8*inch]*4)
    cont.setStyle(TableStyle([
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
    ]))
    return cont


# ── Bloque resumen IA ──────────────────────────────────────────────────────────
def _bloque_resumen(texto):
    header = Table([[
        Paragraph('Resumen Ejecutivo',
                  S('rh', fontSize=10, fontName='Helvetica-Bold', textColor=WHITE)),
        Paragraph('powered by Groq · Llama 3.1',
                  S('rg', fontSize=7.5, textColor=colors.HexColor('#c9b8f0'),
                    alignment=TA_RIGHT, fontName='Helvetica')),
    ]], colWidths=[PAGE_W*0.55, PAGE_W*0.45])
    header.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_PURPLE),
        ('TOPPADDING',    (0,0),(-1,-1), 9),
        ('BOTTOMPADDING', (0,0),(-1,-1), 9),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))

    body = Table([[
        Paragraph(texto.strip(),
                  S('rb', fontSize=9.5, leading=15, textColor=C_DARK_T,
                    alignment=TA_JUSTIFY)),
    ]], colWidths=[PAGE_W])
    body.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_PURP_L),
        ('TOPPADDING',    (0,0),(-1,-1), 12),
        ('BOTTOMPADDING', (0,0),(-1,-1), 12),
        ('LEFTPADDING',   (0,0),(-1,-1), 14),
        ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ('LINEBEFORE',    (0,0),(0,-1),  4, C_PURPLE),
    ]))
    return KeepTogether([header, body])


# ── Tarjetas de recomendaciones (2 columnas) ───────────────────────────────────
PALETA_RECS = [
    (C_BLUE,   C_BLUE_L),
    (C_GREEN,  C_GREEN_L),
    (C_ORANGE, C_ORANGE_L),
    (C_PURPLE, C_PURP_L),
    (C_RED,    C_RED_L),
    (C_GREEN,  C_GREEN_L),
]

def _tarjeta_rec(num, rec, color, bg):
    t = Table([
        [Paragraph(f'{num}. {rec["titulo"]}',
                   S(f'rt{num}', fontSize=9, fontName='Helvetica-Bold', textColor=WHITE))],
        [Paragraph(rec['detalle'],
                   S(f'rd{num}', fontSize=8.5, leading=13, textColor=C_DARK_T,
                     alignment=TA_JUSTIFY))],
    ], colWidths=[COL2_L])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,0),  color),
        ('BACKGROUND',    (0,1),(0,1),  bg),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('LINEBELOW',     (0,-1),(-1,-1), 1, color),
    ]))
    return t


def _recomendaciones(recs):
    if not recs:
        return []
    out = []
    # Pares de 2 columnas
    for i in range(0, len(recs), 2):
        izq = _tarjeta_rec(i+1, recs[i], *PALETA_RECS[i % len(PALETA_RECS)])
        if i+1 < len(recs):
            der = _tarjeta_rec(i+2, recs[i+1], *PALETA_RECS[(i+1) % len(PALETA_RECS)])
        else:
            der = Paragraph('', S('vacio'))

        fila = Table([[izq, der]],
                     colWidths=[COL2_L + COL2_GAP, COL2_R])
        fila.setStyle(TableStyle([
            ('VALIGN',       (0,0),(-1,-1), 'TOP'),
            ('LEFTPADDING',  (0,0),(-1,-1), 0),
            ('RIGHTPADDING', (0,0),(-1,-1), 0),
            ('TOPPADDING',   (0,0),(-1,-1), 0),
            ('BOTTOMPADDING',(0,0),(-1,-1), 0),
        ]))
        out.append(fila)
        out.append(Spacer(1, 0.1*inch))
    return out


# ── Conclusión ─────────────────────────────────────────────────────────────────
def _conclusion(texto):
    t = Table([[
        Paragraph('Conclusion:',
                  S('clt', fontSize=9, fontName='Helvetica-Bold', textColor=C_BLUE)),
        Paragraph(texto.strip(),
                  S('clb', fontSize=9, leading=14, textColor=C_DARK_T,
                    alignment=TA_JUSTIFY)),
    ]], colWidths=[1.1*inch, PAGE_W - 1.1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_BLUE_L),
        ('TOPPADDING',    (0,0),(-1,-1), 11),
        ('BOTTOMPADDING', (0,0),(-1,-1), 11),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ('LINEBEFORE',    (0,0),(0,-1),  3, C_BLUE),
    ]))
    return t


# ── Tabla productos + categorías lado a lado ───────────────────────────────────
def _tabla_productos(productos):
    CAB = S('pc', fontSize=8, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER)
    CEL = S('pd', fontSize=8, textColor=C_DARK_T)
    NUM = S('pn', fontSize=8, textColor=C_DARK_T, alignment=TA_CENTER)

    max_qty = max((p['cantidad'] for p in productos), default=1)
    filas   = [[Paragraph('#', CAB), Paragraph('Producto', CAB),
                Paragraph('Uds.', CAB), Paragraph('Tendencia', CAB)]]

    for i, p in enumerate(productos, 1):
        pct = (p['cantidad'] / max_qty) * 100
        barra = BarraProgreso(pct, C_GREEN, width=1.1*inch, height=9)
        filas.append([
            Paragraph(str(i), NUM),
            Paragraph(p['nombre'], CEL),
            Paragraph(str(p['cantidad']), NUM),
            barra,
        ])

    t = Table(filas, colWidths=[0.3*inch, 2.0*inch, 0.45*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_GREEN),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, C_GREEN_L]),
        ('GRID',          (0,0),(-1,-1), 0.3, colors.HexColor('#dee2e6')),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    return t


def _tabla_categorias(categorias):
    CAB = S('cc', fontSize=8, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER)
    CEL = S('cd', fontSize=8, textColor=C_DARK_T)
    NUM = S('cn', fontSize=8, textColor=C_DARK_T, alignment=TA_CENTER)

    filas = [[Paragraph('Categoria', CAB),
              Paragraph('Uds.', CAB),
              Paragraph('Part.%', CAB),
              Paragraph('Dist.', CAB)]]

    for c in categorias:
        barra = BarraProgreso(c['porcentaje'], C_PURPLE, width=0.9*inch, height=9)
        filas.append([
            Paragraph(c['nombre'], CEL),
            Paragraph(str(c['cantidad']), NUM),
            Paragraph(f"{c['porcentaje']}%", NUM),
            barra,
        ])

    t = Table(filas, colWidths=[1.5*inch, 0.45*inch, 0.55*inch, 1.0*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_PURPLE),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, C_PURP_L]),
        ('GRID',          (0,0),(-1,-1), 0.3, colors.HexColor('#dee2e6')),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ]))
    return t


def _seccion_mini(texto, color):
    return [
        Paragraph(texto, S(f'sm{texto}', fontSize=9, fontName='Helvetica-Bold',
                            textColor=color, spaceBefore=4, spaceAfter=3)),
        HRFlowable(width='100%', thickness=1, color=color, spaceAfter=4),
    ]


def _bloque_datos(productos, categorias):
    """Productos y categorías en 2 columnas."""
    # Columna izquierda
    col_izq = []
    col_izq += _seccion_mini('Top Productos Mas Vendidos', C_GREEN)
    if productos:
        col_izq.append(_tabla_productos(productos))
    else:
        col_izq.append(Paragraph('Sin datos.', S('nd1', fontSize=8, textColor=C_GREY)))

    # Columna derecha
    col_der = []
    col_der += _seccion_mini('Ventas por Categoria', C_PURPLE)
    if categorias:
        col_der.append(_tabla_categorias(categorias))
    else:
        col_der.append(Paragraph('Sin datos.', S('nd2', fontSize=8, textColor=C_GREY)))

    izq_t = Table([[e] for e in col_izq], colWidths=[COL2_L])
    izq_t.setStyle(TableStyle([
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 2),
    ]))

    der_t = Table([[e] for e in col_der], colWidths=[COL2_R])
    der_t.setStyle(TableStyle([
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 2),
    ]))

    cont = Table([[izq_t, der_t]],
                 colWidths=[COL2_L + COL2_GAP, COL2_R])
    cont.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
    ]))
    return cont


# ── Alertas de stock ───────────────────────────────────────────────────────────
def _tabla_stock(alertas):
    CAB = S('sc', fontSize=8, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_CENTER)
    CEL = S('sd', fontSize=8, textColor=C_DARK_T)
    NUM = S('sn', fontSize=8, textColor=C_DARK_T, alignment=TA_CENTER)

    filas = [[
        Paragraph('Producto',     CAB),
        Paragraph('Stock',        CAB),
        Paragraph('Precio Unit.', CAB),
        Paragraph('Estado',       CAB),
        Paragraph('Accion',       CAB),
    ]]

    for p in alertas:
        if p['stock'] == 0:
            estado, color_e, accion = 'AGOTADO',  C_RED,    'Reposicion urgente'
        elif p['stock'] <= 3:
            estado, color_e, accion = 'CRITICO',  C_RED,    'Reponer esta semana'
        else:
            estado, color_e, accion = 'BAJO',     C_ORANGE, 'Programar reposicion'

        filas.append([
            Paragraph(p['nombre'], CEL),
            Paragraph(str(p['stock']), NUM),
            Paragraph(f"${p['precio']:,.2f}", NUM),
            Paragraph(estado, S(f'se{p["id"]}', fontSize=8, fontName='Helvetica-Bold',
                                textColor=color_e, alignment=TA_CENTER)),
            Paragraph(accion, S(f'sa{p["id"]}', fontSize=7.5, textColor=C_GREY,
                                alignment=TA_CENTER)),
        ])

    t = Table(filas, colWidths=[2.7*inch, 0.65*inch, 1.0*inch, 1.1*inch, 1.65*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  C_RED),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, C_RED_L]),
        ('GRID',          (0,0),(-1,-1), 0.3, colors.HexColor('#dee2e6')),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
    ]))
    return t


# ── Título de sección principal ────────────────────────────────────────────────
def _titulo(texto, color=C_BLUE):
    return [
        Spacer(1, 0.16*inch),
        Paragraph(texto, S(f'T{texto}', fontSize=11, fontName='Helvetica-Bold',
                            textColor=color, spaceAfter=3)),
        HRFlowable(width='100%', thickness=1.5, color=color, spaceAfter=5),
    ]


# ── Footer ─────────────────────────────────────────────────────────────────────
def _footer(fecha_str):
    t = Table([[
        Paragraph('Floreria Examen  |  Reporte de uso interno',
                  S('fl', fontSize=7, textColor=C_GREY)),
        Paragraph(f'Groq · Llama 3.1  |  {fecha_str}',
                  S('fr', fontSize=7, textColor=C_PURPLE, alignment=TA_RIGHT)),
    ]], colWidths=[PAGE_W*0.5, PAGE_W*0.5])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), C_GREY_L),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('LINEABOVE',     (0,0),(-1,0),  0.8, colors.HexColor('#ced4da')),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    return t


# ── Función pública ────────────────────────────────────────────────────────────
def generar_reporte_dashboard_pdf(kpis, mas_vendidos, categorias, alertas_stock, analisis):
    """
    Genera el Reporte Ejecutivo PDF del Dashboard IA.

    Args:
        analisis (dict | str): Dict {resumen, recomendaciones, conclusion} o str.
    Returns:
        BytesIO
    """
    if isinstance(analisis, str):
        analisis = {'resumen': analisis, 'recomendaciones': [], 'conclusion': ''}

    buffer   = BytesIO()
    fecha_str = datetime.now().strftime('%d/%m/%Y  %H:%M')

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.5*inch, bottomMargin=0.5*inch,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
    )

    E = [] 

    # 1. Encabezado
    E += _header(fecha_str)

    # 2. KPIs
    E += _titulo('Indicadores Clave (KPIs)', C_BLUE)
    E.append(_kpis(kpis))

    # 3. Resumen IA
    if analisis.get('resumen'):
        E += _titulo('Resumen Ejecutivo  —  Groq IA', C_PURPLE)
        E.append(_bloque_resumen(analisis['resumen']))

    # 4. Recomendaciones IA en 2 columnas
    if analisis.get('recomendaciones'):
        E += _titulo('Recomendaciones de Negocio  —  Groq IA', C_BLUE)
        E += _recomendaciones(analisis['recomendaciones'])

    # 5. Conclusión
    if analisis.get('conclusion'):
        E.append(Spacer(1, 0.08*inch))
        E.append(_conclusion(analisis['conclusion']))

    # 6. Datos: productos + categorías lado a lado
    E += _titulo('Analisis de Ventas', C_GREEN)
    E.append(_bloque_datos(mas_vendidos, categorias))

    # 7. Alertas de stock
    E += _titulo('Alertas de Inventario  —  Requieren Atencion', C_RED)
    if alertas_stock:
        E.append(_tabla_stock(alertas_stock))
    else:
        E.append(Paragraph(
            'Todo el inventario esta en niveles saludables. No se requieren acciones.',
            S('ok', fontSize=9, textColor=C_GREEN, fontName='Helvetica-Bold'),
        ))

    # 8. Footer
    E.append(Spacer(1, 0.2*inch))
    E.append(_footer(fecha_str))

    doc.build(E)
    buffer.seek(0)
    return buffer
