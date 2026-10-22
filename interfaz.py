# INTERFAZ CONSTRUIDA CON LAYOUTS: SE ADAPTA AL TAMAÑO DE LA VENTANA Y AL ZOOM DE LA PANTALLA
import os
import math
from PyQt6 import sip
from PyQt6.QtCore import (Qt, QRegularExpression, QDate, QByteArray, QTimer, QEvent, QRectF, QPointF, QPoint, QSize, pyqtSignal,
                          QPropertyAnimation, QParallelAnimationGroup, QEasingCurve)
from PyQt6.QtGui import (QPixmap, QRegularExpressionValidator, QIcon, QPainter, QColor, QFont, QFontDatabase,
                         QFontMetrics, QPen, QPainterPath, QLinearGradient, QPalette)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QScrollArea,
                             QHeaderView, QAbstractItemView, QBoxLayout, QHBoxLayout, QVBoxLayout, QGridLayout, QStackedWidget,
                             QButtonGroup, QCheckBox, QDateEdit, QDialog, QGraphicsDropShadowEffect, QStyledItemDelegate,
                             QStyle, QToolTip, QGraphicsOpacityEffect)

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
# PALETAS DEL SISTEMA: TODOS LOS COLORES SALEN DE AQUI. TEMA ES LA PALETA EN USO (CLARA U OSCURA)
TEMAS = {
    "claro": {
        "primario": "#147186", "primario_oscuro": "#0f5a6b", "primario_suave": "#e2f0f3",
        "acento": "#147186", # TEXTOS E ICONOS DEL COLOR DE LA MARCA
        "sobre_primario": "#ffffff",
        "menu": "#1b2028", "menu_hover": "#2a313c", "menu_texto": "#c3c9d1", "menu_tenue": "#7d8693",
        "fondo": "#f4f6f8", "superficie": "#ffffff", "hover": "#f6f8fa",
        "borde": "#e4e7eb", "borde_fuerte": "#cdd2d8",
        "texto": "#1b2028", "texto_suave": "#5b6470", "texto_tenue": "#6e7681",
        "exito": "#13734a", "exito_suave": "#e3f4ea",
        "aviso": "#a15c07", "aviso_suave": "#fdf0d5",
        "peligro": "#b42318", "peligro_suave": "#fde8e6", "peligro_borde": "#f1b5ae", "error_fondo": "#fffbfa",
        "neutro": "#4b5563", "neutro_suave": "#eef1f4",
        "deshabilitado": "#edf0f3", "flechas": "flecha",
        "grafico": "#007c9c", # BARRAS DE LOS GRAFICOS: MAS SATURADO QUE EL PRIMARIO PARA DESTACAR SOBRE EL BLANCO
    },
    "oscuro": { # NO ES UNA INVERSION: CADA COLOR SE ELIGIO PARA LEERSE BIEN SOBRE FONDO OSCURO
        "primario": "#147186", "primario_oscuro": "#0f5a6b", "primario_suave": "#173a44",
        "acento": "#5cc6de",
        "sobre_primario": "#ffffff",
        "menu": "#0f1318", "menu_hover": "#1f2630", "menu_texto": "#b4bcc6", "menu_tenue": "#7d8693",
        "fondo": "#14181e", "superficie": "#1c2128", "hover": "#232a33",
        "borde": "#2c333d", "borde_fuerte": "#3b4450",
        "texto": "#e6e9ed", "texto_suave": "#a9b1bb", "texto_tenue": "#8b94a0",
        "exito": "#4cc38a", "exito_suave": "#173528",
        "aviso": "#f0b44c", "aviso_suave": "#3a2c12",
        "peligro": "#f2756a", "peligro_suave": "#3d1d1b", "peligro_borde": "#7a3530", "error_fondo": "#2a1b1b",
        "neutro": "#b4bcc6", "neutro_suave": "#2a313b",
        "deshabilitado": "#262c35", "flechas": "flecha_clara",
        "grafico": "#2aa3c2",
    },
}
TEMA = dict(TEMAS["claro"])
tema_actual = "claro"
ANIMACIONES = True # FUNDIDO AL CAMBIAR DE PANTALLA, AVISOS QUE ENTRAN DESLIZANDO Y MENU QUE SE CONTRAE SUAVE
# LOS DOCUMENTOS (BOLETA, PDF Y EXCEL) SIEMPRE USAN LOS COLORES CLAROS: SE IMPRIMEN SOBRE PAPEL BLANCO
COLOR_PRIMARIO, COLOR_PELIGRO = TEMAS["claro"]["primario"], TEMAS["claro"]["peligro"]
ROL_ETIQUETA = Qt.ItemDataRole.UserRole + 1
ROL_CODIGO = Qt.ItemDataRole.UserRole + 2 # CODIGO DEL REGISTRO DE CADA FILA (LA POSICION CAMBIA AL ORDENAR)
ROL_ORDEN = Qt.ItemDataRole.UserRole + 3 # VALOR REAL PARA ORDENAR (NUMERO O FECHA), NO EL TEXTO MOSTRADO

def ruta(*partes):
    return os.path.join(DIRECTORIO, *partes)
def ruta_qss(*partes): # QSS USA "/" EN LAS RUTAS, TAMBIEN EN WINDOWS
    return ruta(*partes).replace("\\", "/")
def estilo():
    t = TEMA
    return f"""
* {{ font-family: "Inter", "Segoe UI", sans-serif; }}
QWidget {{ color: {t['texto']}; font-size: 10pt; }}
QMainWindow, QDialog, QStackedWidget > QWidget {{ background: {t['fondo']}; }}
QToolTip {{ background: {t['menu']}; color: #ffffff; border: none; padding: 6px 8px; }}
/* MENU LATERAL */
QFrame#menu {{ background: {t['menu']}; }}
QFrame#menu QLabel {{ color: #ffffff; background: transparent; }}
QLabel#marca {{ font-size: 12pt; font-weight: 700; }}
QFrame#menu QLabel#marca_icono {{ background: {t['primario']}; border-radius: 9px; }}
QLabel#seccion_menu {{ color: {t['menu_tenue']}; font-size: 8pt; font-weight: 600; padding: 14px 12px 6px 12px; }}
QFrame#menu QPushButton {{ color: {t['menu_texto']}; background: transparent; border: none; text-align: left;
                          padding: 9px 12px; border-radius: 8px; font-weight: 500; }}
QFrame#menu QPushButton:hover {{ background: {t['menu_hover']}; color: #ffffff; }}
QFrame#menu QPushButton:checked {{ background: {t['primario']}; color: #ffffff; font-weight: 600; }}
QFrame#linea_menu {{ background: {t['menu_hover']}; }}
QFrame#menu QPushButton[tipo="icono_menu"] {{ padding: 0px; border-radius: 8px; }}
QFrame#menu QLabel#avatar {{ background: {t['primario']}; color: #ffffff; border-radius: 17px; font-weight: 700; font-size: 9pt; }}
QLabel#sesion_nombre {{ font-weight: 600; }}
QFrame#menu QLabel#sesion_rol {{ color: {t['menu_tenue']}; font-size: 8.5pt; }}
/* TEXTOS */
QLabel#titulo {{ font-size: 19pt; font-weight: 700; }}
QLabel#subtitulo {{ color: {t['texto_suave']}; }}
QLabel#tenue {{ color: {t['texto_tenue']}; font-size: 9pt; }}
QLabel#total {{ font-size: 18pt; font-weight: 700; color: {t['acento']}; }}
QLabel#etiqueta_campo {{ font-weight: 600; font-size: 9pt; color: {t['texto_suave']}; }}
QLabel#ayuda {{ color: {t['texto_tenue']}; font-size: 8.5pt; }}
QLabel#error {{ color: {t['peligro']}; font-size: 8.5pt; font-weight: 500; }}
QLabel#vacio_texto {{ color: {t['texto_tenue']}; }}
/* TARJETAS E INDICADORES */
QFrame#tarjeta {{ background: {t['superficie']}; border: 1px solid {t['borde']}; border-radius: 12px; }}
QFrame#tarjeta QLabel, QFrame#tarjeta QCheckBox {{ background: transparent; }}
QLabel#titulo_tarjeta {{ font-size: 11pt; font-weight: 600; }}
QLabel#valor_indicador {{ font-size: 16pt; font-weight: 700; }}
QLabel#icono_indicador {{ background: {t['primario_suave']}; border-radius: 15px; }}
QFrame#tarjeta[clicable="true"]:hover {{ border-color: {t['primario']}; }}
QLabel#tendencia {{ font-size: 8.5pt; font-weight: 600; color: {t['texto_suave']}; }}
QLabel#tendencia[sentido="sube"] {{ color: {t['exito']}; }}
QLabel#tendencia[sentido="baja"] {{ color: {t['peligro']}; }}
QFrame#fila_ranking {{ border-radius: 8px; }}
QFrame#fila_ranking[clicable="true"]:hover {{ background: {t['hover']}; }}
QLabel#cifra {{ font-size: 13pt; font-weight: 700; }}
QFrame#sello {{ background: {t['peligro_suave']}; border: 1px solid {t['peligro_borde']}; border-radius: 8px; }}
QFrame#sello QLabel {{ color: {t['peligro']}; }}
QLabel#titulo_sello {{ font-weight: 700; letter-spacing: 1px; }}
/* INICIO DE SESION */
QWidget#panel_login QLabel {{ color: #ffffff; background: transparent; }}
QLabel#marca_login {{ font-size: 22pt; font-weight: 700; }}
QLabel#lema_login {{ font-size: 11pt; }}
QWidget#formulario_login {{ background: {t['superficie']}; }}
QLineEdit[tamano="grande"] {{ padding: 9px 10px; }}
/* PANTALLA DE BLOQUEO */
QWidget#bloqueo {{ background: {t['fondo']}; }}
QFrame#tarjeta QLabel#avatar_bloqueo {{ background: {t['primario']}; color: #ffffff; border-radius: 32px; font-size: 18pt; font-weight: 700; }}
/* CAMPOS */
QLineEdit, QComboBox, QSpinBox, QDateEdit {{ background: {t['superficie']}; border: 1px solid {t['borde_fuerte']}; border-radius: 8px;
                                            padding: 6px 10px; min-height: 22px; selection-background-color: {t['primario']}; }}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDateEdit:hover {{ border-color: {t['texto_tenue']}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{ border-color: {t['acento']}; }}
QLineEdit[error="true"], QComboBox[error="true"], QSpinBox[error="true"] {{ border-color: {t['peligro']}; background: {t['error_fondo']}; }}
QLineEdit:read-only {{ background: {t['neutro_suave']}; color: {t['texto_suave']}; border-color: {t['borde']}; }}
QSpinBox {{ padding-right: 26px; }}
QSpinBox::up-button, QSpinBox::down-button {{ subcontrol-origin: border; width: 24px; background: transparent; border-left: 1px solid {t['borde']}; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-bottom: 1px solid {t['borde']}; border-top-right-radius: 8px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 8px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {t['hover']}; }}
QSpinBox::up-arrow {{ image: url("{ruta_qss('iconos', t['flechas'] + '_arriba.svg')}"); width: 10px; height: 6px; }}
QSpinBox::down-arrow, QComboBox::down-arrow, QDateEdit::down-arrow {{ image: url("{ruta_qss('iconos', t['flechas'] + '_abajo.svg')}"); width: 10px; height: 6px; }}
QComboBox, QDateEdit {{ padding-right: 28px; }}
QComboBox::drop-down, QDateEdit::drop-down {{ subcontrol-origin: border; subcontrol-position: center right; width: 26px; border: none; }}
QComboBox QAbstractItemView {{ background: {t['superficie']}; border: 1px solid {t['borde']}; selection-background-color: {t['primario_suave']};
                              selection-color: {t['texto']}; outline: 0; padding: 4px; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {t['borde_fuerte']}; border-radius: 5px; background: {t['superficie']}; }}
QCheckBox::indicator:checked {{ background: {t['primario']}; border-color: {t['primario']}; image: url("{ruta_qss('iconos', 'check.svg')}"); }}
QCalendarWidget QWidget#qt_calendar_navigationbar {{ background: {t['primario']}; }}
QCalendarWidget QToolButton {{ color: #ffffff; background: transparent; font-weight: 600; }}
QCalendarWidget QAbstractItemView {{ background: {t['superficie']}; color: {t['texto']}; selection-background-color: {t['primario']}; selection-color: #ffffff; }}
QMenu {{ background: {t['superficie']}; border: 1px solid {t['borde']}; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {t['primario_suave']}; color: {t['texto']}; }}
QMenu::item:disabled {{ color: {t['texto_tenue']}; }}
QMenu::separator {{ height: 1px; background: {t['borde']}; margin: 4px 8px; }}
/* BOTONES */
QPushButton {{ background: {t['superficie']}; border: 1px solid {t['borde_fuerte']}; border-radius: 8px; padding: 8px 14px; font-weight: 600; }}
QPushButton:hover {{ background: {t['hover']}; border-color: {t['texto_tenue']}; }}
QPushButton[tipo="primario"] {{ background: {t['primario']}; color: {t['sobre_primario']}; border-color: {t['primario']}; }}
QPushButton[tipo="primario"]:hover {{ background: {t['primario_oscuro']}; border-color: {t['primario_oscuro']}; }}
QPushButton[tipo="peligro"] {{ color: {t['peligro']}; border-color: {t['peligro_borde']}; }}
QPushButton[tipo="peligro"]:hover {{ background: {t['peligro_suave']}; border-color: {t['peligro']}; }}
QPushButton[tamano="grande"] {{ padding: 12px 22px; font-size: 11pt; }}
QPushButton:disabled, QPushButton[tipo="primario"]:disabled, QPushButton[tipo="peligro"]:disabled {{
    background: {t['deshabilitado']}; color: {t['texto_tenue']}; border-color: {t['deshabilitado']}; }}
/* TABLAS */
QTableWidget {{ background: {t['superficie']}; border: none; selection-background-color: {t['primario_suave']};
               selection-color: {t['texto']}; outline: 0; }}
QTableWidget::item {{ padding: 0px 8px; border-bottom: 1px solid {t['borde']}; }}
QTableWidget::item:selected {{ background: {t['primario_suave']}; color: {t['texto']}; }}
QHeaderView {{ background: {t['superficie']}; }}
QHeaderView::section {{ background: {t['superficie']}; color: {t['texto_suave']}; font-size: 8.5pt; font-weight: 600;
                       padding: 8px 10px; border: none; border-bottom: 1px solid {t['borde_fuerte']}; }}
QHeaderView::section:hover {{ color: {t['texto']}; }}
QHeaderView::up-arrow, QHeaderView::down-arrow {{ subcontrol-origin: padding; subcontrol-position: top center; width: 8px; height: 5px; top: 2px; }} /* ARRIBA: NO CHOCA CON EL TEXTO */
QHeaderView::up-arrow {{ image: url("{ruta_qss('iconos', t['flechas'] + '_arriba.svg')}"); }}
QHeaderView::down-arrow {{ image: url("{ruta_qss('iconos', t['flechas'] + '_abajo.svg')}"); }}
QTableCornerButton::section {{ background: {t['superficie']}; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: {t['borde_fuerte']}; border-radius: 3px; min-height: 30px; min-width: 30px; }}
QScrollBar::handle:hover {{ background: {t['texto_tenue']}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ width: 0; height: 0; background: none; }}
/* NUEVA VENTA: TICKET */
QFrame#separador {{ border: none; border-top: 1px dashed {t['borde_fuerte']}; background: transparent; }}
QFrame#linea_venta {{ background: transparent; border: none; border-bottom: 1px solid {t['borde']}; }}
QLabel#producto_linea {{ font-weight: 600; }}
QLabel#subtotal_linea {{ font-weight: 700; }}
QFrame#chip {{ background: {t['primario_suave']}; border: none; border-radius: 10px; }}
QFrame#chip[vacio="true"] {{ background: {t['neutro_suave']}; }}
QFrame#tarjeta QLabel#iniciales {{ background: {t['primario']}; color: #ffffff; border-radius: 17px; font-weight: 700; font-size: 9pt; }}
QFrame#tarjeta QLabel#iniciales[vacio="true"] {{ background: {t['borde_fuerte']}; }}
QLabel#etiqueta_total {{ font-size: 11pt; font-weight: 700; color: {t['texto_suave']}; }}
QLabel#monto_ticket {{ font-size: 22pt; font-weight: 700; color: {t['acento']}; }}
QLabel#monto_ticket[anulada="true"] {{ color: {t['texto_tenue']}; text-decoration: line-through; }}
QLabel#vuelto {{ font-weight: 700; color: {t['exito']}; }}
QLabel#vuelto[falta="true"] {{ color: {t['peligro']}; }}
QScrollArea#detalle_venta, QWidget#contenido_detalle {{ background: transparent; border: none; }}
QPushButton[tipo="segmento"] {{ border-radius: 0px; padding: 7px 18px; }}
QPushButton[tipo="segmento"]:checked {{ background: {t['primario']}; color: #ffffff; border-color: {t['primario']}; }}
QPushButton[lado="izquierdo"] {{ border-top-left-radius: 8px; border-bottom-left-radius: 8px; }}
QPushButton[lado="derecho"] {{ border-top-right-radius: 8px; border-bottom-right-radius: 8px; }}
QPushButton[tipo="enlace"] {{ border: none; background: transparent; color: {t['texto_suave']}; font-weight: 500; }}
QPushButton[tipo="enlace"]:hover {{ color: {t['peligro']}; background: transparent; }}
QPushButton[tipo="enlace"]:disabled {{ color: {t['borde_fuerte']}; background: transparent; border: none; }}
QPushButton[tipo="icono"] {{ border: none; background: transparent; padding: 4px; border-radius: 6px; }}
QPushButton[tipo="icono"]:hover {{ background: {t['peligro_suave']}; }}
QSpinBox[readOnly="true"] {{ background: {t['neutro_suave']}; color: {t['texto_suave']}; border-color: {t['borde']}; }}
/* NOTIFICACIONES */
QFrame#notificacion {{ background: {t['superficie']}; border: 1px solid {t['borde']}; border-radius: 10px; }}
QFrame#notificacion[tipo="exito"] {{ border-left: 4px solid {t['exito']}; }}
QFrame#notificacion[tipo="aviso"] {{ border-left: 4px solid {t['aviso']}; }}
QFrame#notificacion[tipo="error"] {{ border-left: 4px solid {t['peligro']}; }}
QFrame#notificacion QLabel {{ background: transparent; }}
QLabel#titulo_notificacion {{ font-weight: 700; }}
QFrame#notificacion QPushButton {{ border: none; background: transparent; padding: 2px; }}
"""

# FUENTES E ICONOS
def carga_fuentes(): # INTER VIENE CON EL PROYECTO: SE VE IGUAL EN CUALQUIER PC
    for archivo in sorted(os.listdir(ruta("fuentes"))):
        if archivo.endswith(".ttf"):
            QFontDatabase.addApplicationFont(ruta("fuentes", archivo))
    return "Inter" in QFontDatabase.families()
_iconos = {}
def pixmap_icono(nombre, color, tam=64):
    svg = open(ruta("iconos", "lucide", f"{nombre}.svg"), encoding="utf-8").read().replace("currentColor", color)
    imagen = QPixmap(tam, tam)
    imagen.fill(Qt.GlobalColor.transparent)
    pintor = QPainter(imagen)
    pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(pintor)
    pintor.end()
    return imagen
def icono(nombre, color=None, color_activo=None): # ICONO LUCIDE PINTADO DEL COLOR PEDIDO
    color = color or TEMA["texto"]
    clave = (nombre, color, color_activo)
    if clave not in _iconos:
        resultado = QIcon()
        resultado.addPixmap(pixmap_icono(nombre, color), QIcon.Mode.Normal, QIcon.State.Off)
        if color_activo:
            resultado.addPixmap(pixmap_icono(nombre, color_activo), QIcon.Mode.Normal, QIcon.State.On)
        _iconos[clave] = resultado
    return _iconos[clave]
def icono_aplicacion():
    return QIcon(ruta("iconos", "app.ico"))

# TEMA CLARO U OSCURO: EL ESTILO SE ARMA CON LA PALETA EN USO Y LOS ICONOS SE VUELVEN A PINTAR AL CAMBIARLA
_con_tema = [] # (WIDGET DUEÑO, FUNCION QUE LE APLICA LOS COLORES)
def con_tema(dueno, aplicar): # APLICA AHORA Y OTRA VEZ CADA VEZ QUE CAMBIA EL TEMA
    aplicar()
    _con_tema.append((dueno, aplicar))
    if len(_con_tema) % 500 == 0: # LAS LINEAS DE VENTA SE CREAN Y BORRAN TODO EL DIA: SE OLVIDAN LAS QUE YA NO EXISTEN
        _con_tema[:] = [(d, f) for d, f in _con_tema if not sip.isdeleted(d)]
def paleta(): # PARA LO QUE NO CUBRE EL ESTILO: MENUS CONTEXTUALES, CALENDARIO, CUADROS DE DIALOGO DEL SISTEMA
    t, p = TEMA, QPalette()
    for rol, color in ((QPalette.ColorRole.Window, t["fondo"]), (QPalette.ColorRole.WindowText, t["texto"]), (QPalette.ColorRole.Base, t["superficie"]),
                       (QPalette.ColorRole.AlternateBase, t["hover"]), (QPalette.ColorRole.Text, t["texto"]), (QPalette.ColorRole.Button, t["superficie"]),
                       (QPalette.ColorRole.ButtonText, t["texto"]), (QPalette.ColorRole.Highlight, t["primario"]), (QPalette.ColorRole.HighlightedText, "#ffffff"),
                       (QPalette.ColorRole.ToolTipBase, t["menu"]), (QPalette.ColorRole.ToolTipText, "#ffffff"), (QPalette.ColorRole.PlaceholderText, t["texto_tenue"]),
                       (QPalette.ColorRole.Link, t["acento"])):
        p.setColor(rol, QColor(color))
    for rol in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, rol, QColor(t["texto_tenue"]))
    return p
def aplica_tema(app, nombre):
    global tema_actual
    tema_actual = nombre if nombre in TEMAS else "claro"
    TEMA.clear()
    TEMA.update(TEMAS[tema_actual])
    if hasattr(app.styleHints(), "setColorScheme"): # QT 6.8+: TAMBIEN LA BARRA DE TITULO DE WINDOWS
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark if tema_actual == "oscuro" else Qt.ColorScheme.Light)
    app.setPalette(paleta())
    app.setStyleSheet(estilo())
    _con_tema[:] = [(d, f) for d, f in _con_tema if not sip.isdeleted(d)]
    for _, aplicar in _con_tema:
        aplicar()

# AYUDANTES
def repule(widget): # VUELVE A APLICAR EL ESTILO TRAS CAMBIAR UNA PROPIEDAD
    widget.style().unpolish(widget)
    widget.style().polish(widget)
def crea_titulo(texto, subtitulo=None):
    caja = QVBoxLayout()
    caja.setSpacing(2)
    titulo = QLabel(texto)
    titulo.setObjectName("titulo")
    caja.addWidget(titulo)
    if subtitulo:
        sub = QLabel(subtitulo)
        sub.setObjectName("subtitulo")
        caja.addWidget(sub)
    return caja
def crea_boton(texto, tipo=None, nombre_icono=None, grande=False):
    boton = QPushButton(texto)
    if tipo:
        boton.setProperty("tipo", tipo)
    if grande:
        boton.setProperty("tamano", "grande")
    if nombre_icono:
        con_tema(boton, lambda: boton.setIcon(icono(nombre_icono, {"primario": TEMA["sobre_primario"], "peligro": TEMA["peligro"]}.get(tipo, TEMA["texto"]))))
        boton.setIconSize(QSize(18, 18) if grande else QSize(16, 16))
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    return boton
def crea_buscador(texto):
    buscador = QLineEdit()
    buscador.setPlaceholderText(texto)
    buscador.setClearButtonEnabled(True)
    icono_campo(buscador, "search")
    return buscador
def icono_campo(campo, nombre, posicion=QLineEdit.ActionPosition.LeadingPosition): # ICONO DENTRO DE UN CAMPO DE TEXTO
    accion = campo.addAction(icono(nombre, TEMA["texto_tenue"]), posicion)
    con_tema(campo, lambda: accion.setIcon(icono(accion.property("icono") or nombre, TEMA["texto_tenue"])))
    return accion
def ojo_clave(campo): # EL OJO MUESTRA U OCULTA LA CONTRASEÑA
    accion = icono_campo(campo, "eye", QLineEdit.ActionPosition.TrailingPosition)
    accion.setToolTip("Mostrar contraseña")
    def alterna():
        oculta = campo.echoMode() == QLineEdit.EchoMode.Password
        campo.setEchoMode(QLineEdit.EchoMode.Normal if oculta else QLineEdit.EchoMode.Password)
        accion.setProperty("icono", "eye-off" if oculta else "eye")
        accion.setIcon(icono(accion.property("icono"), TEMA["texto_tenue"]))
        accion.setToolTip("Ocultar contraseña" if oculta else "Mostrar contraseña")
    accion.triggered.connect(alterna)
    return accion
def pon_pixmap(etiqueta, nombre, clave_color, tam): # ICONO DIBUJADO EN UNA ETIQUETA, DEL COLOR DEL TEMA
    con_tema(etiqueta, lambda: etiqueta.setPixmap(pixmap_icono(nombre, TEMA[clave_color], tam * 2).scaled(
        tam, tam, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
def crea_texto(placeholder="", maximo=255, solo_digitos=None, patron=None):
    campo = QLineEdit()
    campo.setPlaceholderText(placeholder)
    campo.setMaxLength(maximo)
    if solo_digitos: # SOLO PERMITE ESCRIBIR HASTA N DIGITOS
        patron = rf"\d{{0,{solo_digitos}}}"
    if patron:
        campo.setValidator(QRegularExpressionValidator(QRegularExpression(patron)))
    return campo
def crea_clave(placeholder="Contraseña"):
    campo = QLineEdit()
    campo.setPlaceholderText(placeholder)
    campo.setEchoMode(QLineEdit.EchoMode.Password)
    return campo
def crea_combo(opciones): # opciones: [(texto visible, dato guardado)]
    combo = QComboBox()
    for texto, dato in opciones:
        combo.addItem(texto, dato)
    return combo
def crea_fecha(fecha):
    campo = QDateEdit(fecha)
    campo.setCalendarPopup(True)
    campo.setDisplayFormat("dd/MM/yyyy")
    return campo
def con_etiqueta(texto, widget): # ETIQUETA PEQUEÑA ENCIMA DE UN FILTRO
    caja = QVBoxLayout()
    caja.setSpacing(4)
    etiqueta = QLabel(texto)
    etiqueta.setObjectName("etiqueta_campo")
    caja.addWidget(etiqueta)
    caja.addWidget(widget)
    return caja
def sombra(widget, opacidad=22, desenfoque=24):
    efecto = QGraphicsDropShadowEffect(widget)
    efecto.setBlurRadius(desenfoque)
    efecto.setOffset(0, 2)
    efecto.setColor(QColor(16, 24, 40, opacidad))
    widget.setGraphicsEffect(efecto)

# COMPONENTES
class Tarjeta(QFrame): # CONTENEDOR BLANCO CON BORDE SUAVE Y TITULO OPCIONAL
    def __init__(self, titulo=None):
        super().__init__()
        self.setObjectName("tarjeta")
        self.caja = QVBoxLayout(self)
        self.caja.setContentsMargins(18, 16, 18, 16)
        self.caja.setSpacing(12)
        self.cabecera = QHBoxLayout()
        self.lbl_titulo = QLabel(titulo or "")
        self.lbl_titulo.setObjectName("titulo_tarjeta")
        self.lbl_titulo.setVisible(bool(titulo))
        self.cabecera.addWidget(self.lbl_titulo)
        self.cabecera.addStretch()
        self.caja.addLayout(self.cabecera)
    def setTitle(self, texto):
        self.lbl_titulo.setText(texto)
        self.lbl_titulo.setVisible(bool(texto))
    def title(self):
        return self.lbl_titulo.text()
    def addWidget(self, widget, estiramiento=0):
        self.caja.addWidget(widget, estiramiento)
    def addLayout(self, layout, estiramiento=0):
        self.caja.addLayout(layout, estiramiento)

class Campo(QWidget): # ETIQUETA ENCIMA, CAMPO, AYUDA Y ERROR DEBAJO
    def __init__(self, etiqueta, widget, obligatorio=False, ayuda=""):
        super().__init__()
        caja = QVBoxLayout(self)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(4)
        self.lbl = QLabel()
        self.lbl.setObjectName("etiqueta_campo")
        con_tema(self.lbl, lambda: self.lbl.setText(etiqueta + (f" <span style='color:{TEMA['peligro']}'>*</span>" if obligatorio else "")))
        self.widget = widget
        self.texto_ayuda = ayuda
        self.ayuda = QLabel(ayuda)
        self.ayuda.setObjectName("ayuda")
        self.ayuda.setVisible(bool(ayuda))
        self.error = QLabel()
        self.error.setObjectName("error")
        self.error.setWordWrap(True)
        self.error.hide()
        caja.addWidget(self.lbl)
        caja.addWidget(widget)
        caja.addWidget(self.ayuda)
        caja.addWidget(self.error)
        for senal in ("textEdited", "currentIndexChanged", "valueChanged", "toggled"): # SE LIMPIA APENAS SE CORRIGE
            if hasattr(widget, senal):
                getattr(widget, senal).connect(self.limpia_error)
                break
    def muestra_error(self, texto):
        self.error.setText(texto)
        self.error.show()
        self.ayuda.hide()
        self.widget.setProperty("error", True)
        repule(self.widget)
    def limpia_error(self, *_):
        self.error.hide()
        self.ayuda.setVisible(bool(self.texto_ayuda))
        if self.widget.property("error"):
            self.widget.setProperty("error", False)
            repule(self.widget)
    def tiene_error(self):
        return not self.error.isHidden()
    def cambia_ayuda(self, texto):
        self.texto_ayuda = texto
        self.ayuda.setText(texto)
        self.ayuda.setVisible(bool(texto) and not self.tiene_error())

class DelegadoTabla(QStyledItemDelegate): # RESALTA LA FILA BAJO EL MOUSE Y DIBUJA LAS ETIQUETAS DE ESTADO
    def paint(self, pintor, opcion, indice):
        tabla = self.parent()
        seleccionada = bool(opcion.state & QStyle.StateFlag.State_Selected)
        if indice.row() == tabla.fila_hover and not seleccionada:
            pintor.fillRect(opcion.rect, QColor(TEMA["hover"]))
        etiqueta = indice.data(ROL_ETIQUETA)
        if not etiqueta:
            super().paint(pintor, opcion, indice)
            return
        if seleccionada:
            pintor.fillRect(opcion.rect, QColor(TEMA["primario_suave"]))
        pintor.save()
        pintor.setPen(QColor(TEMA["borde"]))
        pintor.drawLine(opcion.rect.bottomLeft(), opcion.rect.bottomRight())
        fondo, color = TEMA[f"{etiqueta}_suave"], TEMA["acento" if etiqueta == "primario" else etiqueta]
        texto = indice.data(Qt.ItemDataRole.DisplayRole)
        fuente = QFont(opcion.font)
        fuente.setPointSizeF(max(fuente.pointSizeF() - 1, 7))
        fuente.setWeight(QFont.Weight.DemiBold)
        medidas = QFontMetrics(fuente)
        ancho, alto = medidas.horizontalAdvance(texto) + 18, medidas.height() + 6
        alineacion = indice.data(Qt.ItemDataRole.TextAlignmentRole)
        derecha = alineacion is not None and bool(int(getattr(alineacion, "value", alineacion)) & Qt.AlignmentFlag.AlignRight.value)
        x =opcion.rect.right() - 10 - ancho if derecha else opcion.rect.left() + 10
        caja = QRectF(x, opcion.rect.center().y() - alto / 2 + 1, ancho, alto)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QColor(fondo))
        pintor.drawRoundedRect(caja, alto / 2, alto / 2)
        pintor.setPen(QColor(color))
        pintor.setFont(fuente)
        pintor.drawText(caja, Qt.AlignmentFlag.AlignCenter, texto)
        pintor.restore()
    def sizeHint(self, opcion, indice):
        tam = super().sizeHint(opcion, indice)
        if indice.data(ROL_ETIQUETA):
            tam.setWidth(max(tam.width(), QFontMetrics(opcion.font).horizontalAdvance(str(indice.data())) + 40))
        return tam

class ItemTabla(QTableWidgetItem): # "S/ 750.00" VA ANTES QUE "S/ 2,500.00" Y LAS FECHAS SE ORDENAN POR FECHA
    def __lt__(self, otro):
        a, b = self.data(ROL_ORDEN), otro.data(ROL_ORDEN)
        if a is not None and b is not None:
            return a < b
        return self.text().casefold() < otro.text().casefold()

class Tabla(QTableWidget): # TABLA DE SOLO LECTURA, SIN CUADRICULA, CON ESTADO VACIO
    def __init__(self, encabezados, columna_ancha, texto_vacio="", derecha=(), ordenable=False):
        super().__init__(0, len(encabezados))
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # SE EDITA EN EL FORMULARIO
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(42)
        encabezado = self.horizontalHeader()
        encabezado.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        encabezado.setHighlightSections(False)
        self.configura_columnas(encabezados, columna_ancha, derecha)
        self.ordenable = ordenable
        if ordenable: # CLIC EN EL ENCABEZADO: ASCENDENTE, DESCENDENTE Y DE NUEVO SIN ORDEN
            encabezado.setSortIndicatorClearable(True)
            encabezado.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            encabezado.setSectionsClickable(True)
            encabezado.setCursor(Qt.CursorShape.PointingHandCursor)
            encabezado.setToolTip("Haz clic en una columna para ordenar")
            self.setSortingEnabled(True)
        self.fila_hover = -1
        self.setMouseTracking(True)
        self.setItemDelegate(DelegadoTabla(self))
        # ESTADO VACIO: ICONO Y TEXTO GUIA EN LUGAR DE UNA TABLA EN BLANCO
        self.vacio = QWidget(self.viewport())
        caja = QVBoxLayout(self.vacio)
        caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
        imagen = QLabel()
        pon_pixmap(imagen, "inbox", "borde_fuerte", 40)
        imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio = QLabel()
        self.lbl_vacio.setObjectName("vacio_texto")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.setWordWrap(True)
        self.lbl_vacio.setMinimumWidth(320)
        caja.addWidget(imagen)
        caja.addWidget(self.lbl_vacio)
        self.mostrar_vacio(texto_vacio)
    def configura_columnas(self, encabezados, columna_ancha, derecha=()): # LA MISMA TABLA PUEDE MOSTRAR OTRAS COLUMNAS (REPORTES)
        super().setRowCount(0)
        self.setColumnCount(len(encabezados))
        self.setHorizontalHeaderLabels([texto.upper() for texto in encabezados])
        for columna in range(len(encabezados)): # LOS NUMEROS VAN A LA DERECHA Y SU ENCABEZADO TAMBIEN
            lado = Qt.AlignmentFlag.AlignRight if columna in derecha else Qt.AlignmentFlag.AlignLeft
            self.horizontalHeaderItem(columna).setTextAlignment(lado | Qt.AlignmentFlag.AlignVCenter)
        encabezado = self.horizontalHeader()
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        encabezado.setSectionResizeMode(columna_ancha, QHeaderView.ResizeMode.Stretch) # ESTA COLUMNA OCUPA EL ESPACIO LIBRE
        if self.isSortingEnabled():
            encabezado.setSortIndicator(-1, Qt.SortOrder.AscendingOrder) # EL ORDEN ANTERIOR NO APLICA A LAS NUEVAS COLUMNAS
    def llena(self, datos, celdas, codigo_elegido=None):
        # LLENA LA TABLA SIN DISPARAR EVENTOS, RESPETA EL ORDEN ELEGIDO Y VUELVE A MARCAR SOLO EL REGISTRO ELEGIDO
        self.blockSignals(True)
        self.setSortingEnabled(False) # MIENTRAS SE LLENA, ORDENAR MOVERIA LAS FILAS A MEDIO CAMINO
        self.clearSelection()
        self.setRowCount(len(datos))
        for fila, registro in enumerate(datos):
            items = celdas(registro)
            items[0].setData(ROL_CODIGO, registro[0])
            for columna, item in enumerate(items):
                self.setItem(fila, columna, item)
        if self.ordenable:
            self.setSortingEnabled(True)
        self.clearSelection()
        self.setCurrentItem(None)
        fila = self.fila_de_codigo(codigo_elegido)
        if fila is not None:
            self.selectRow(fila)
        self.blockSignals(False)
    def codigo_en_fila(self, fila):
        item = self.item(fila, 0)
        return None if item is None else item.data(ROL_CODIGO)
    def fila_de_codigo(self, codigo):
        if codigo is None:
            return None
        for fila in range(self.rowCount()):
            if self.codigo_en_fila(fila) == codigo:
                return fila
        return None
    def codigo_seleccionado(self):
        seleccion = self.selectionModel().selectedRows()
        return self.codigo_en_fila(seleccion[0].row()) if seleccion else None
    def mostrar_vacio(self, texto):
        self.lbl_vacio.setText(texto)
        self._actualiza_vacio()
    def setRowCount(self, filas):
        super().setRowCount(filas)
        self._actualiza_vacio()
    def _actualiza_vacio(self):
        self.vacio.setGeometry(self.viewport().rect())
        self.vacio.setVisible(self.rowCount() == 0 and bool(self.lbl_vacio.text()))
    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self.vacio.setGeometry(self.viewport().rect())
    def mouseMoveEvent(self, evento):
        fila = self.indexAt(evento.position().toPoint()).row()
        if fila != self.fila_hover:
            self.fila_hover = fila
            self.viewport().update()
        super().mouseMoveEvent(evento)
    def leaveEvent(self, evento):
        self.fila_hover = -1
        self.viewport().update()
        super().leaveEvent(evento)

class Notificacion(QFrame): # AVISO FLOTANTE ARRIBA A LA DERECHA (LEJOS DE LOS BOTONES DE ACCION) QUE SE CIERRA SOLO
    TITULOS = {"exito": "Listo", "aviso": "Atención", "error": "Error", "info": "Información"}
    ICONOS = {"exito": ("circle-check", "exito"), "aviso": ("triangle-alert", "aviso"), "error": ("circle-alert", "peligro"), "info": ("info", "acento")}
    def __init__(self, padre):
        super().__init__(padre)
        self.setObjectName("notificacion")
        self.setFixedWidth(380)
        caja = QHBoxLayout(self)
        caja.setContentsMargins(14, 12, 10, 12)
        caja.setSpacing(12)
        self.lbl_icono = QLabel()
        self.lbl_icono.setFixedSize(22, 22)
        textos = QVBoxLayout()
        textos.setSpacing(2)
        self.lbl_titulo = QLabel()
        self.lbl_titulo.setObjectName("titulo_notificacion")
        self.lbl_texto = QLabel()
        self.lbl_texto.setWordWrap(True)
        self.lbl_texto.setFixedWidth(270)
        textos.addWidget(self.lbl_titulo)
        textos.addWidget(self.lbl_texto)
        self.btn_cerrar = QPushButton()
        con_tema(self.btn_cerrar, lambda: self.btn_cerrar.setIcon(icono("x", TEMA["texto_tenue"])))
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.clicked.connect(self.hide)
        caja.addWidget(self.lbl_icono, 0, Qt.AlignmentFlag.AlignTop)
        caja.addLayout(textos, 1)
        caja.addWidget(self.btn_cerrar, 0, Qt.AlignmentFlag.AlignTop)
        sombra(self, 40, 30)
        self.temporizador = QTimer(self)
        self.temporizador.setSingleShot(True)
        self.temporizador.timeout.connect(self.hide)
        padre.installEventFilter(self)
        self.hide()
    def muestra(self, texto, tipo="exito", titulo=None, duracion=5000):
        self.setProperty("tipo", tipo)
        repule(self)
        nombre, color = self.ICONOS[tipo]
        self.lbl_icono.setPixmap(pixmap_icono(nombre, TEMA[color], 44).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.lbl_titulo.setText(titulo or self.TITULOS[tipo])
        self.lbl_texto.setText(texto)
        self.lbl_texto.setFixedHeight(self.lbl_texto.heightForWidth(self.lbl_texto.width()) + 4) # ALTURA DEL TEXTO YA ENVUELTO
        self.adjustSize()
        self.posiciona()
        if ANIMACIONES and not self.isVisible(): # ENTRA DESLIZANDOSE DESDE LA DERECHA
            final = self.pos()
            self.move(final + QPoint(32, 0))
            self.animacion = QPropertyAnimation(self, b"pos", self)
            self.animacion.setDuration(180)
            self.animacion.setEndValue(final)
            self.animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animacion.start()
        self.show()
        self.raise_()
        self.temporizador.start(duracion + 40 * len(texto)) # LOS MENSAJES LARGOS DURAN MAS
    def posiciona(self):
        if getattr(self, "animacion", None) is not None:
            self.animacion.stop()
        padre = self.parentWidget().rect()
        self.move(padre.width() - self.width() - 24, 20)
    def eventFilter(self, objeto, evento):
        if evento.type() == QEvent.Type.Resize and self.isVisible():
            self.posiciona()
        return False

class Indicador(QFrame): # TARJETA DEL PANEL DE INICIO CON ICONO, VALOR, DETALLE Y TENDENCIA; PUEDE ABRIR OTRA PANTALLA
    pulsado = pyqtSignal()
    def __init__(self, titulo, nombre_icono):
        super().__init__()
        self.setObjectName("tarjeta")
        textos = QVBoxLayout(self) # EL ICONO VA ARRIBA A LA DERECHA: EL MONTO USA TODO EL ANCHO
        textos.setContentsMargins(18, 14, 18, 14)
        textos.setSpacing(2)
        arriba = QHBoxLayout()
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("subtitulo")
        circulo = QLabel()
        circulo.setObjectName("icono_indicador")
        circulo.setFixedSize(30, 30)
        circulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pon_pixmap(circulo, nombre_icono, "acento", 16)
        arriba.addWidget(etiqueta, 1)
        arriba.addWidget(circulo)
        self.valor = QLabel("-")
        self.valor.setObjectName("valor_indicador")
        self.detalle = QLabel()
        self.detalle.setObjectName("tenue")
        self.tendencia = QLabel()
        self.tendencia.setObjectName("tendencia")
        self.tendencia.hide()
        textos.addLayout(arriba)
        textos.addWidget(self.valor)
        textos.addWidget(self.detalle)
        textos.addWidget(self.tendencia)
        textos.addStretch()
        self.clicable = False
    def muestra_tendencia(self, texto, sentido=None, ayuda=""): # LA FLECHA Y EL SIGNO DICEN EL SENTIDO; EL COLOR SOLO LO REFUERZA
        self.tendencia.setText(texto)
        self.tendencia.setToolTip(ayuda)
        self.tendencia.setProperty("sentido", sentido or "")
        repule(self.tendencia)
        self.tendencia.setVisible(bool(texto))
    def hazlo_clicable(self, clicable, ayuda=""):
        self.clicable = clicable
        self.setProperty("clicable", clicable)
        self.setCursor(Qt.CursorShape.PointingHandCursor if clicable else Qt.CursorShape.ArrowCursor)
        self.setToolTip(ayuda if clicable else "")
        repule(self)
    def mouseReleaseEvent(self, evento):
        if self.clicable and evento.button() == Qt.MouseButton.LeftButton and self.rect().contains(evento.position().toPoint()):
            self.pulsado.emit()
        super().mouseReleaseEvent(evento)

def monto_compacto(valor): # EJE DEL GRAFICO: S/ 500, S/ 2.5K, S/ 1.2M
    valor = float(valor)
    if valor >= 1_000_000:
        return f"S/ {valor / 1_000_000:g}M"
    if valor >= 1000:
        return f"S/ {valor / 1000:g}K"
    return f"S/ {valor:g}"

class GraficoBarras(QWidget): # COLUMNAS DE UNA SOLA SERIE: SIN LEYENDA (LA NOMBRA EL TITULO), TOOLTIP EN TODA LA COLUMNA
    IZQUIERDA, DERECHA, ARRIBA, ABAJO = 58, 8, 10, 26
    def __init__(self, texto_vacio="Sin ventas en este periodo."):
        super().__init__()
        self.setMinimumHeight(190)
        self.setMouseTracking(True)
        self.datos = [] # [(etiqueta del eje, valor, tooltip)]
        self.texto_vacio = texto_vacio
        self.hover = -1
    def muestra(self, datos):
        self.datos = list(datos)
        self.hover = -1
        self.update()
    def area(self):
        return QRectF(self.IZQUIERDA, self.ARRIBA, self.width() - self.IZQUIERDA - self.DERECHA, self.height() - self.ARRIBA - self.ABAJO)
    def escala(self): # TOPE Y MARCAS REDONDAS DEL EJE Y
        maximo = max((float(valor) for _, valor, _ in self.datos), default=0)
        if maximo <= 0:
            return 0, []
        bruto = maximo / 4
        magnitud = 10 ** math.floor(math.log10(bruto))
        paso = next(m * magnitud for m in (1, 2, 2.5, 5, 10) if m * magnitud >= bruto)
        tope = paso * math.ceil(maximo / paso)
        return tope, [paso * i for i in range(int(round(tope / paso)) + 1)]
    def indice_en(self, x):
        area = self.area()
        if not self.datos or x < area.left() or x > area.right():
            return -1
        return min(int((x - area.left()) / (area.width() / len(self.datos))), len(self.datos) - 1)
    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = self.area()
        fuente = QFont(self.font())
        fuente.setPointSizeF(8.5)
        pintor.setFont(fuente)
        tope, marcas = self.escala()
        if tope == 0:
            pintor.setPen(QColor(TEMA["texto_tenue"]))
            pintor.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.texto_vacio)
            return
        for marca in marcas: # LINEAS DE GUIA FINAS, SOLIDAS Y DISCRETAS
            y = area.bottom() - marca / tope * area.height()
            pintor.setPen(QPen(QColor(TEMA["borde"]), 1))
            pintor.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            pintor.setPen(QColor(TEMA["texto_tenue"]))
            pintor.drawText(QRectF(0, y - 9, self.IZQUIERDA - 8, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, monto_compacto(marca))
        ranura = area.width() / len(self.datos)
        grosor = min(24.0, ranura * 0.6)
        for indice, (_, valor, _) in enumerate(self.datos):
            if float(valor) <= 0:
                continue
            alto = float(valor) / tope * area.height()
            x = area.left() + indice * ranura + (ranura - grosor) / 2
            color = QColor(TEMA["grafico"])
            if indice == self.hover:
                color = color.lighter(125) # LA BARRA RESPONDE AL MOUSE
            alto = max(alto, 2.0) # UN MONTO PEQUEÑO SIGUE VIENDOSE
            radio = min(4.0, alto, grosor / 2)
            arriba, base = area.bottom() - alto, area.bottom()
            forma = QPainterPath() # PUNTA REDONDEADA, BASE RECTA SOBRE EL EJE
            forma.moveTo(x, base)
            forma.lineTo(x, arriba + radio)
            forma.quadTo(x, arriba, x + radio, arriba)
            forma.lineTo(x + grosor - radio, arriba)
            forma.quadTo(x + grosor, arriba, x + grosor, arriba + radio)
            forma.lineTo(x + grosor, base)
            forma.closeSubpath()
            pintor.fillPath(forma, color)
        pintor.setPen(QColor(TEMA["texto_tenue"])) # ETIQUETAS DEL EJE X SIN CHOCAR: SE SALTEAN SI NO CABEN
        cada = max(1, math.ceil(len(self.datos) / max(1, int(area.width() // 48))))
        for indice in range(0, len(self.datos), cada):
            x = area.left() + indice * ranura
            pintor.drawText(QRectF(x - 20, area.bottom() + 4, ranura + 40, self.ABAJO - 4), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.datos[indice][0])
    def mouseMoveEvent(self, evento):
        indice = self.indice_en(evento.position().x())
        if indice != self.hover:
            self.hover = indice
            self.update()
        if indice >= 0:
            QToolTip.showText(evento.globalPosition().toPoint(), self.datos[indice][2], self)
        else:
            QToolTip.hideText()
    def leaveEvent(self, evento):
        self.hover = -1
        self.update()
        QToolTip.hideText()

class Medidor(QWidget): # BARRA FINA PROPORCIONAL; EL FONDO ES UN PASO MAS CLARO DEL MISMO COLOR
    def __init__(self):
        super().__init__()
        self.setFixedHeight(6)
        self.fraccion = 0.0
    def paintEvent(self, evento):
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(QColor(TEMA["primario_suave"]))
        pintor.drawRoundedRect(QRectF(self.rect()), 3, 3)
        if self.fraccion > 0:
            pintor.setBrush(QColor(TEMA["grafico"]))
            pintor.drawRoundedRect(QRectF(0, 0, max(6.0, self.width() * self.fraccion), self.height()), 3, 3)

class FilaRanking(QFrame): # NOMBRE, VALOR Y MEDIDOR; AL HACER CLIC ABRE EL PRODUCTO
    elegida = pyqtSignal(object)
    def __init__(self, codigo, nombre, detalle, fraccion, clicable):
        super().__init__()
        self.setObjectName("fila_ranking")
        self.setProperty("clicable", clicable)
        if clicable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip("Ver el producto")
        self.clicable = clicable
        self.codigo = codigo
        caja = QVBoxLayout(self)
        caja.setContentsMargins(8, 5, 8, 5)
        caja.setSpacing(4)
        textos = QHBoxLayout()
        self.lbl_nombre = QLabel(nombre)
        self.lbl_nombre.setObjectName("producto_linea")
        self.lbl_detalle = QLabel(detalle)
        self.lbl_detalle.setObjectName("tenue")
        textos.addWidget(self.lbl_nombre, 1)
        textos.addWidget(self.lbl_detalle)
        self.medidor = Medidor()
        self.medidor.fraccion = fraccion
        caja.addLayout(textos)
        caja.addWidget(self.medidor)
    def mousePressEvent(self, evento):
        if self.clicable and evento.button() == Qt.MouseButton.LeftButton:
            self.elegida.emit(self.codigo)

class ListaRanking(QWidget): # LOS MAS VENDIDOS COMO LISTA COMPACTA CON MEDIDORES
    elegida = pyqtSignal(object)
    def __init__(self, texto_vacio):
        super().__init__()
        self.caja = QVBoxLayout(self)
        self.caja.setContentsMargins(0, 0, 0, 0)
        self.caja.setSpacing(2)
        self.lbl_vacio = QLabel(texto_vacio)
        self.lbl_vacio.setObjectName("vacio_texto")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caja.addWidget(self.lbl_vacio)
        self.caja.addStretch()
        self.filas = []
    def muestra(self, datos, clicable=False): # datos: [(codigo, nombre, detalle, fraccion 0..1)]
        for fila in self.filas:
            fila.setParent(None)
            fila.deleteLater()
        self.filas = []
        for codigo, nombre, detalle, fraccion in datos:
            fila = FilaRanking(codigo, nombre, detalle, fraccion, clicable)
            fila.elegida.connect(self.elegida.emit)
            self.caja.insertWidget(self.caja.count() - 1, fila)
            self.filas.append(fila)
        self.lbl_vacio.setVisible(not datos)

class SelectorPeriodo(QWidget): # PERIODOS RAPIDOS Y RANGO PERSONALIZADO; AVISA CON cambio
    cambio = pyqtSignal()
    PERIODOS = ["Hoy", "Esta semana", "Este mes", "Mes anterior", "Personalizado"]
    def __init__(self, inicial="Este mes"):
        super().__init__()
        caja = QHBoxLayout(self)
        caja.setContentsMargins(0, 0, 0, 0)
        caja.setSpacing(12)
        self.cmb_periodo = QComboBox()
        self.cmb_periodo.addItems(self.PERIODOS)
        self.desde = crea_fecha(QDate.currentDate())
        self.hasta = crea_fecha(QDate.currentDate())
        caja.addLayout(con_etiqueta("Periodo", self.cmb_periodo))
        caja.addLayout(con_etiqueta("Desde", self.desde))
        caja.addLayout(con_etiqueta("Hasta", self.hasta))
        self.cmb_periodo.setCurrentText(inicial)
        self.aplica_periodo()
        self.cmb_periodo.currentIndexChanged.connect(self.aplica_periodo)
        self.desde.dateChanged.connect(self.fechas_cambiadas)
        self.hasta.dateChanged.connect(self.fechas_cambiadas)
    @staticmethod
    def rango(nombre, hoy):
        if nombre == "Hoy":
            return hoy, hoy
        if nombre == "Esta semana": # DE LUNES A DOMINGO
            lunes = hoy.addDays(1 - hoy.dayOfWeek())
            return lunes, lunes.addDays(6)
        primero = QDate(hoy.year(), hoy.month(), 1)
        if nombre == "Mes anterior":
            primero = primero.addMonths(-1)
        return primero, primero.addDays(primero.daysInMonth() - 1)
    def aplica_periodo(self, *_):
        nombre = self.cmb_periodo.currentText()
        if nombre == "Personalizado":
            return
        inicio, fin = self.rango(nombre, QDate.currentDate())
        for campo, fecha in ((self.desde, inicio), (self.hasta, fin)):
            campo.blockSignals(True)
            campo.setDate(fecha)
            campo.blockSignals(False)
        self.cambio.emit()
    def fechas_cambiadas(self, *_): # TOCAR UNA FECHA A MANO = PERIODO PERSONALIZADO
        self.cmb_periodo.blockSignals(True)
        self.cmb_periodo.setCurrentText("Personalizado")
        self.cmb_periodo.blockSignals(False)
        self.cambio.emit()
    def fija(self, nombre, desde=None, hasta=None): # SIN AVISAR: QUIEN LO LLAMA BUSCA DESPUES
        self.blockSignals(True)
        self.cmb_periodo.blockSignals(True)
        self.cmb_periodo.setCurrentText(nombre)
        self.cmb_periodo.blockSignals(False)
        if desde is None:
            self.aplica_periodo()
        else:
            for campo, fecha in ((self.desde, desde), (self.hasta, hasta)):
                campo.blockSignals(True)
                campo.setDate(fecha)
                campo.blockSignals(False)
        self.blockSignals(False)
    def fechas(self):
        return self.desde.date().toPyDate(), self.hasta.date().toPyDate()

class LineaDetalle(QFrame): # LINEA DE UNA VENTA YA REGISTRADA (SOLO LECTURA)
    def __init__(self, producto, cantidad_precio, subtotal):
        super().__init__()
        self.setObjectName("linea_venta")
        rejilla = QGridLayout(self)
        rejilla.setContentsMargins(0, 8, 0, 8)
        rejilla.setHorizontalSpacing(10)
        rejilla.setVerticalSpacing(2)
        self.lbl_producto = QLabel(producto)
        self.lbl_producto.setObjectName("producto_linea")
        self.lbl_producto.setWordWrap(True)
        self.lbl_producto.setTextFormat(Qt.TextFormat.PlainText)
        self.lbl_cantidad = QLabel(cantidad_precio)
        self.lbl_cantidad.setObjectName("tenue")
        self.lbl_subtotal = QLabel(subtotal)
        self.lbl_subtotal.setObjectName("subtotal_linea")
        rejilla.addWidget(self.lbl_producto, 0, 0)
        rejilla.addWidget(self.lbl_cantidad, 1, 0)
        rejilla.addWidget(self.lbl_subtotal, 0, 1, 2, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        rejilla.setColumnStretch(0, 1)

class PanelImagen(QWidget): # FOTO DE LA TIENDA CON UN VELO TURQUESA Y LA MARCA ENCIMA
    def __init__(self):
        super().__init__()
        self.setObjectName("panel_login")
        self.imagen = QPixmap(ruta("inicio_logo.jpg"))
        caja = QVBoxLayout(self)
        caja.setContentsMargins(36, 36, 36, 36)
        caja.addStretch()
        marca = QLabel("LGD Technologies")
        marca.setObjectName("marca_login")
        lema = QLabel("Sistema de ventas e inventario")
        lema.setObjectName("lema_login")
        caja.addWidget(marca)
        caja.addWidget(lema)
    def paintEvent(self, evento):
        pintor = QPainter(self)
        if not self.imagen.isNull(): # LA FOTO CUBRE TODO EL PANEL, RECORTADA AL CENTRO
            escalada = self.imagen.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            pintor.drawPixmap(0, 0, escalada, (escalada.width() - self.width()) // 2, (escalada.height() - self.height()) // 2, self.width(), self.height())
        velo = QLinearGradient(0, 0, 0, self.height())
        velo.setColorAt(0, QColor(20, 113, 134, 70))
        velo.setColorAt(1, QColor(12, 74, 88, 235))
        pintor.fillRect(self.rect(), velo)

class PaginaCrud(QWidget): # TABLA CON BUSCADOR A LA IZQUIERDA Y FORMULARIO A LA DERECHA
    def __init__(self, titulo, subtitulo, encabezados, columna_ancha, texto_busqueda, campos, derecha=(0,)):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        layout.addLayout(crea_titulo(titulo, subtitulo))
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(20)
        lista = Tarjeta()
        self.buscador = crea_buscador(texto_busqueda)
        self.tabla = Tabla(encabezados, columna_ancha, derecha=derecha, ordenable=True)
        self.lbl_conteo = QLabel()
        self.lbl_conteo.setObjectName("tenue")
        self.barra = QHBoxLayout() # BUSCADOR Y FILTROS EXTRA DE LA PANTALLA
        self.barra.setSpacing(14)
        self.barra.addWidget(self.buscador, 1)
        lista.addLayout(self.barra)
        lista.addWidget(self.tabla, 1)
        lista.addWidget(self.lbl_conteo)
        self.columna_izquierda = QVBoxLayout()
        self.columna_izquierda.setSpacing(20)
        self.columna_izquierda.addWidget(lista, 1)
        self.grupo = Tarjeta(" ")
        self.campos, self.contenedores = {}, {}
        for clave, etiqueta, widget, obligatorio, ayuda in campos:
            contenedor = Campo(etiqueta, widget, obligatorio, ayuda)
            self.grupo.addWidget(contenedor)
            self.campos[clave] = widget
            self.contenedores[clave] = contenedor
        self.btn_nuevo = crea_boton("Nuevo", nombre_icono="plus")
        self.btn_guardar = crea_boton("Guardar", "primario", "save")
        self.btn_eliminar = crea_boton("Eliminar", "peligro", "trash-2")
        botones = QHBoxLayout()
        botones.addWidget(self.btn_eliminar)
        botones.addStretch()
        botones.addWidget(self.btn_nuevo)
        botones.addWidget(self.btn_guardar)
        self.grupo.caja.addSpacing(4)
        self.grupo.addLayout(botones)
        derecha = QVBoxLayout()
        derecha.addWidget(self.grupo)
        derecha.addStretch()
        cuerpo.addLayout(self.columna_izquierda, 3)
        cuerpo.addLayout(derecha, 2)
        layout.addLayout(cuerpo, 1)

def crea_separador(): # LINEA PUNTEADA COMO EN UN TICKET
    linea = QFrame()
    linea.setObjectName("separador")
    linea.setFixedHeight(2)
    return linea
def campos_cliente(con_codigo=True): # LOS MISMOS CAMPOS EN LA PANTALLA CLIENTES Y EN "NUEVO CLIENTE" DE LA VENTA
    campos = [
        ("nombre", "Nombre", crea_texto("Nombre y apellido"), True, ""),
        ("dni", "DNI", crea_texto("Ej.: 12345678", 8, solo_digitos=8), True, "8 dígitos"),
        ("telefono", "Teléfono", crea_texto("Ej.: 987654321", 9, solo_digitos=9), True, "9 dígitos"),
        ("sexo", "Sexo", crea_combo([("Selecciona…", None), ("Masculino", "MASCULINO"), ("Femenino", "FEMENINO")]), True, ""),
    ]
    if con_codigo:
        codigo = QLineEdit()
        codigo.setReadOnly(True) # LO ASIGNA LA BASE DE DATOS
        campos.insert(0, ("codigo", "Código", codigo, False, "Lo asigna el sistema"))
    return campos

class LineaVenta(QFrame): # UNA LINEA DEL TICKET: PRODUCTO, PRECIO, CANTIDAD EDITABLE, SUBTOTAL Y QUITAR
    def __init__(self, codigo, producto, precio, cantidad, maximo):
        super().__init__()
        self.setObjectName("linea_venta")
        self.codigo = codigo
        rejilla = QGridLayout(self) # NOMBRE Y PRECIO A LA IZQUIERDA; CANTIDAD, SUBTOTAL Y QUITAR EN LA MISMA FILA
        rejilla.setContentsMargins(0, 8, 0, 8)
        rejilla.setHorizontalSpacing(10)
        rejilla.setVerticalSpacing(2)
        self.lbl_producto = QLabel(producto)
        self.lbl_producto.setObjectName("producto_linea")
        self.lbl_producto.setWordWrap(True) # EL NOMBRE COMPLETO, AUNQUE SEA LARGO
        self.lbl_precio = QLabel(f"{precio} c/u")
        self.lbl_precio.setObjectName("tenue")
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, max(maximo, 1))
        self.spn_cantidad.setValue(cantidad)
        self.spn_cantidad.setFixedWidth(84)
        self.spn_cantidad.setToolTip(f"Disponibles: {maximo}")
        self.lbl_subtotal = QLabel()
        self.lbl_subtotal.setObjectName("subtotal_linea")
        self.lbl_subtotal.setMinimumWidth(96)
        self.lbl_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.btn_quitar = QPushButton()
        self.btn_quitar.setProperty("tipo", "icono")
        con_tema(self.btn_quitar, lambda: self.btn_quitar.setIcon(icono("x", TEMA["texto_tenue"])))
        self.btn_quitar.setToolTip("Quitar de la venta")
        self.btn_quitar.setCursor(Qt.CursorShape.PointingHandCursor)
        rejilla.addWidget(self.lbl_producto, 0, 0)
        rejilla.addWidget(self.lbl_precio, 1, 0)
        rejilla.addWidget(self.spn_cantidad, 0, 1, 2, 1, Qt.AlignmentFlag.AlignVCenter)
        rejilla.addWidget(self.lbl_subtotal, 0, 2, 2, 1, Qt.AlignmentFlag.AlignVCenter)
        rejilla.addWidget(self.btn_quitar, 0, 3, 2, 1, Qt.AlignmentFlag.AlignVCenter)
        rejilla.setColumnStretch(0, 1)

class DetalleVenta(QScrollArea): # LISTA DE LINEAS DEL TICKET CON DESPLAZAMIENTO Y ESTADO VACIO
    def __init__(self, texto_vacio, nombre_icono="shopping-cart"):
        super().__init__()
        self.setObjectName("detalle_venta")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contenido = QWidget()
        contenido.setObjectName("contenido_detalle")
        self.caja = QVBoxLayout(contenido)
        self.caja.setContentsMargins(0, 0, 6, 0)
        self.caja.setSpacing(0)
        self.vacio = QWidget()
        vacio = QVBoxLayout(self.vacio)
        vacio.setContentsMargins(0, 40, 0, 0)
        imagen = QLabel()
        pon_pixmap(imagen, nombre_icono, "borde_fuerte", 40)
        imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio = QLabel(texto_vacio)
        self.lbl_vacio.setObjectName("vacio_texto")
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.setWordWrap(True)
        vacio.addWidget(imagen)
        vacio.addWidget(self.lbl_vacio)
        self.caja.addWidget(self.vacio)
        self.caja.addStretch()
        self.setWidget(contenido)
        self.lineas = []
    def limpia(self):
        for linea in self.lineas:
            linea.setParent(None)
            linea.deleteLater()
        self.lineas = []
        self.vacio.show()
    def agrega(self, linea):
        self.caja.insertWidget(self.caja.count() - 1, linea) # ANTES DEL ESPACIO FINAL
        self.lineas.append(linea)
        self.vacio.hide()

class DialogoCliente(QDialog): # REGISTRAR UN CLIENTE SIN SALIR DE LA VENTA
    def __init__(self, padre):
        super().__init__(padre)
        self.setWindowTitle("Nuevo cliente")
        self.setFixedWidth(420)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(24, 20, 24, 20)
        caja.setSpacing(12)
        caja.addLayout(crea_titulo("Nuevo cliente", "Quedará elegido para esta venta."))
        self.campos, self.contenedores = {}, {}
        for clave, etiqueta, widget, obligatorio, ayuda in campos_cliente(con_codigo=False):
            contenedor = Campo(etiqueta, widget, obligatorio, ayuda)
            caja.addWidget(contenedor)
            self.campos[clave] = widget
            self.contenedores[clave] = contenedor
        botones = QHBoxLayout()
        self.btn_cancelar = crea_boton("Cancelar")
        self.btn_guardar = crea_boton("Registrar cliente", "primario", "user-plus")
        self.btn_guardar.setDefault(True)
        botones.addStretch()
        botones.addWidget(self.btn_cancelar)
        botones.addWidget(self.btn_guardar)
        caja.addLayout(botones)
        self.btn_cancelar.clicked.connect(self.reject)

class DialogoStock(QDialog): # INGRESO O SALIDA DE MERCADERIA: SUMA O RESTA SOBRE EL STOCK REAL
    def __init__(self, padre, producto, stock):
        super().__init__(padre)
        self.setWindowTitle("Movimiento de stock")
        self.setFixedWidth(420)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(24, 20, 24, 20)
        caja.setSpacing(12)
        caja.addLayout(crea_titulo(producto, f"Stock actual: {stock} unid."))
        self.cmb_tipo = crea_combo([("Ingreso de mercadería (suma)", 1), ("Salida o corrección (resta)", -1)])
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1000000)
        self.spn_cantidad.setSuffix(" unid.")
        caja.addLayout(con_etiqueta("Tipo de movimiento", self.cmb_tipo))
        caja.addLayout(con_etiqueta("Cantidad", self.spn_cantidad))
        self.lbl_resultado = QLabel()
        self.lbl_resultado.setObjectName("subtitulo")
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("error")
        self.lbl_error.setWordWrap(True)
        caja.addWidget(self.lbl_resultado)
        caja.addWidget(self.lbl_error)
        botones = QHBoxLayout()
        self.btn_cancelar = crea_boton("Cancelar")
        self.btn_guardar = crea_boton("Aplicar", "primario", "package-plus")
        self.btn_guardar.setDefault(True)
        botones.addStretch()
        botones.addWidget(self.btn_cancelar)
        botones.addWidget(self.btn_guardar)
        caja.addLayout(botones)
        self.btn_cancelar.clicked.connect(self.reject)

class DialogoLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iniciar sesión - Sistema de Ventas")
        self.setWindowIcon(icono_aplicacion())
        self.setFixedSize(860, 520)
        columnas = QHBoxLayout(self) # IZQUIERDA LA FOTO CON LA MARCA, DERECHA EL FORMULARIO
        columnas.setContentsMargins(0, 0, 0, 0)
        columnas.setSpacing(0)
        columnas.addWidget(PanelImagen(), 1)
        formulario = QWidget()
        formulario.setObjectName("formulario_login")
        formulario.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        formulario.setFixedWidth(400)
        caja = QVBoxLayout(formulario)
        caja.setContentsMargins(44, 40, 44, 40)
        caja.setSpacing(14)
        caja.addStretch()
        caja.addLayout(crea_titulo("Bienvenido", "Ingresa con tu usuario para continuar."))
        caja.addSpacing(6)
        self.txt_usuario = crea_texto("Tu usuario", 30)
        icono_campo(self.txt_usuario, "user-round")
        self.txt_clave = crea_clave("Tu contraseña")
        icono_campo(self.txt_clave, "lock")
        self.accion_ver_clave = ojo_clave(self.txt_clave)
        for campo in (self.txt_usuario, self.txt_clave):
            campo.setProperty("tamano", "grande")
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("error")
        self.lbl_error.setWordWrap(True)
        self.btn_ingresar = crea_boton("Ingresar", "primario", "arrow-right", grande=True)
        self.btn_ingresar.setLayoutDirection(Qt.LayoutDirection.RightToLeft) # LA FLECHA VA DESPUES DEL TEXTO
        self.btn_ingresar.setDefault(True) # ENTER = INGRESAR
        caja.addLayout(con_etiqueta("Usuario", self.txt_usuario))
        caja.addLayout(con_etiqueta("Contraseña", self.txt_clave))
        caja.addWidget(self.lbl_error)
        caja.addWidget(self.btn_ingresar)
        caja.addStretch()
        pie = QLabel("Sistema de Ventas e Inventario")
        pie.setObjectName("tenue")
        pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caja.addWidget(pie)
        columnas.addWidget(formulario)
    def alterna_clave(self):
        self.accion_ver_clave.trigger()

class DialogoClave(QDialog): # obligatorio: AL INGRESAR CON UNA CONTRASEÑA DE EJEMPLO O TEMPORAL (YA LA ESCRIBIO, NO SE PIDE OTRA VEZ)
    def __init__(self, padre, obligatorio=False):
        super().__init__(padre)
        self.setWindowTitle("Cambiar contraseña")
        self.setWindowIcon(icono_aplicacion())
        self.setFixedWidth(420 if obligatorio else 400)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(24, 20, 24, 20)
        caja.setSpacing(12)
        if obligatorio:
            caja.addLayout(crea_titulo("Crea tu contraseña", "Por seguridad, cambia la contraseña inicial."))
        self.txt_actual = crea_clave("Contraseña actual")
        self.txt_nueva = crea_clave("Mínimo 6 caracteres")
        self.txt_repite = crea_clave("Repite la nueva contraseña")
        if not obligatorio:
            caja.addLayout(con_etiqueta("Contraseña actual", self.txt_actual))
        caja.addLayout(con_etiqueta("Nueva contraseña", self.txt_nueva))
        caja.addLayout(con_etiqueta("Repite la nueva contraseña", self.txt_repite))
        ojo_clave(self.txt_nueva)
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("error")
        self.lbl_error.setWordWrap(True)
        botones = QHBoxLayout()
        self.btn_cancelar = crea_boton("Volver al inicio de sesión" if obligatorio else "Cancelar")
        self.btn_guardar = crea_boton("Guardar", "primario", "save")
        self.btn_guardar.setDefault(True)
        botones.addStretch()
        botones.addWidget(self.btn_cancelar)
        botones.addWidget(self.btn_guardar)
        caja.addWidget(self.lbl_error)
        caja.addLayout(botones)
        self.btn_cancelar.clicked.connect(self.reject)

class PantallaBloqueo(QWidget): # TAPA TODA LA VENTANA TRAS UN TIEMPO SIN USO; LA VENTA EN CURSO SIGUE AHI AL VOLVER
    def __init__(self, padre):
        super().__init__(padre)
        self.setObjectName("bloqueo")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        afuera = QVBoxLayout(self)
        afuera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tarjeta = Tarjeta()
        tarjeta.setFixedWidth(380)
        tarjeta.caja.setContentsMargins(32, 28, 32, 28)
        sombra(tarjeta)
        self.lbl_avatar = QLabel()
        self.lbl_avatar.setObjectName("avatar_bloqueo")
        self.lbl_avatar.setFixedSize(64, 64)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo = QLabel("Sesión bloqueada")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_usuario = QLabel()
        self.lbl_usuario.setObjectName("subtitulo")
        self.lbl_usuario.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruccion = QLabel("Escribe tu contraseña para continuar.")
        instruccion.setObjectName("tenue")
        instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_clave = crea_clave("Tu contraseña")
        self.txt_clave.setProperty("tamano", "grande")
        icono_campo(self.txt_clave, "lock")
        ojo_clave(self.txt_clave)
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("error")
        self.lbl_error.setWordWrap(True)
        self.btn_desbloquear = crea_boton("Desbloquear", "primario", "arrow-right", grande=True)
        self.btn_desbloquear.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.btn_cerrar_sesion = crea_boton("Cerrar sesión")
        self.btn_cerrar_sesion.setProperty("tipo", "enlace")
        self.txt_clave.returnPressed.connect(self.btn_desbloquear.click)
        tarjeta.addWidget(self.lbl_avatar, 0)
        tarjeta.caja.setAlignment(self.lbl_avatar, Qt.AlignmentFlag.AlignHCenter)
        tarjeta.addWidget(titulo)
        tarjeta.addWidget(self.lbl_usuario)
        tarjeta.addWidget(instruccion)
        tarjeta.caja.addSpacing(6)
        tarjeta.addLayout(con_etiqueta("Contraseña", self.txt_clave))
        tarjeta.addWidget(self.lbl_error)
        tarjeta.addWidget(self.btn_desbloquear)
        tarjeta.addWidget(self.btn_cerrar_sesion)
        afuera.addWidget(tarjeta)
        padre.installEventFilter(self)
        self.hide()
    def muestra(self, nombre, usuario, iniciales):
        self.lbl_avatar.setText(iniciales)
        self.lbl_usuario.setText(f"{nombre} ({usuario})")
        self.txt_clave.clear()
        self.lbl_error.setText("")
        self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
        self.txt_clave.setFocus()
    def eventFilter(self, objeto, evento):
        if evento.type() == QEvent.Type.Resize:
            self.setGeometry(self.parentWidget().rect())
        return False

class Interfaz:
    def __init__(self, ventana):
        ventana.setWindowTitle("Sistema de Ventas")
        ventana.setWindowIcon(icono_aplicacion())
        ventana.resize(1280, 760)
        ventana.setMinimumSize(1100, 680)
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.crea_menu())
        self.paginas = QStackedWidget()
        self.inicio = self.crea_inicio()
        self.clientes = PaginaCrud("Clientes", "Registra, busca y edita a tus clientes.",
                                   ["Código", "Nombre", "DNI", "Teléfono", "Sexo"], 1, "Buscar por código, nombre o DNI", campos_cliente())
        self.productos = PaginaCrud("Productos", "Administra el catálogo, los precios y el stock.",
                                    ["Código", "Tipo", "Marca", "Precio", "Stock"], 1, "Buscar por código, tipo o marca", [
            ("codigo", "Código", self.crea_codigo(), False, "Lo asigna el sistema"),
            ("tipo", "Tipo", crea_texto("Ej.: Laptop"), True, ""),
            ("marca", "Marca", crea_texto("Ej.: HP"), True, ""),
            ("precio", "Precio (S/)", crea_texto("0.00", 12, patron=r"\d{0,8}([.,]\d{0,2})?"), True, "Usa punto o coma para los decimales"),
            ("stock", "Stock", self.crea_stock(), False, ""),
        ], derecha=(0, 3, 4))
        self.btn_stock = crea_boton("Ingresar o retirar stock…", nombre_icono="package-plus")
        self.productos.grupo.caja.insertWidget(self.productos.grupo.caja.indexOf(self.productos.contenedores["stock"]) + 1, self.btn_stock)
        self.chk_stock_bajo = QCheckBox("Solo stock bajo")
        self.chk_stock_bajo.setToolTip("Productos con 5 unidades o menos")
        self.productos.barra.addWidget(self.chk_stock_bajo)
        self.clientes.columna_izquierda.addWidget(self.crea_compras_cliente()) # DEBAJO DE LA LISTA: EL FORMULARIO CONSERVA SU ALTO
        self.usuarios = PaginaCrud("Usuarios", "Cuentas de acceso al sistema y sus permisos.",
                                   ["Código", "Usuario", "Nombre", "Rol", "Activo"], 2, "Buscar por código, usuario o nombre", [
            ("codigo", "Código", self.crea_codigo(), False, "Lo asigna el sistema"),
            ("usuario", "Usuario", crea_texto("Ej.: jperez", 30, patron=r"[A-Za-z0-9_.]{0,30}"), True, "Sin espacios: letras, números, punto o guion bajo"),
            ("nombre", "Nombre", crea_texto("Nombre completo", 100), True, ""),
            ("rol", "Rol", crea_combo([("Selecciona…", None), ("Administrador", "ADMIN"), ("Vendedor", "VENDEDOR")]), True, ""),
            ("activo", "Estado", QCheckBox("Puede ingresar al sistema"), False, ""),
            ("clave", "Contraseña", crea_clave("Mínimo 6 caracteres"), False, ""),
        ])
        self.venta = self.crea_venta()
        self.ventas = self.crea_historial()
        self.reportes = self.crea_reportes()
        for pagina in (self.inicio, self.clientes, self.productos, self.venta, self.ventas, self.reportes, self.usuarios):
            self.paginas.addWidget(pagina)
        layout.addWidget(self.paginas, 1)
        ventana.setCentralWidget(central)
        self.bloqueo = PantallaBloqueo(central)
        self.notificacion = Notificacion(central)
        self.animacion_pagina = None

    ANCHO_MENU, ANCHO_MENU_CONTRAIDO = 232, 68
    def crea_menu(self):
        menu = QFrame()
        menu.setObjectName("menu")
        menu.setFixedWidth(self.ANCHO_MENU)
        self.menu = menu
        self.menu_contraido = False
        caja = QVBoxLayout(menu)
        caja.setContentsMargins(14, 20, 14, 16)
        caja.setSpacing(2)
        marca = QHBoxLayout()
        marca.setSpacing(10)
        self.logo_menu = QLabel()
        self.logo_menu.setObjectName("marca_icono")
        self.logo_menu.setFixedSize(34, 34)
        self.logo_menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_menu.setPixmap(pixmap_icono("store", "#ffffff", 40).scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.lbl_marca = QLabel("LGD Technologies")
        self.lbl_marca.setObjectName("marca")
        marca.addWidget(self.logo_menu)
        marca.addWidget(self.lbl_marca)
        marca.addStretch()
        caja.addLayout(marca)
        seccion = QHBoxLayout() # "MENU" Y EL BOTON PARA CONTRAERLO
        self.lbl_seccion_menu = QLabel("MENÚ")
        self.lbl_seccion_menu.setObjectName("seccion_menu")
        self.btn_contraer = self.crea_boton_menu("panel-left-close", "Contraer menú")
        seccion.addWidget(self.lbl_seccion_menu)
        seccion.addStretch()
        seccion.addWidget(self.btn_contraer, 0, Qt.AlignmentFlag.AlignBottom)
        caja.addSpacing(6)
        caja.addLayout(seccion)
        caja.addSpacing(2)
        self.opciones_menu = []
        self.grupo_menu = QButtonGroup(menu)
        self.grupo_menu.setExclusive(True)
        self.btn_inicio = self.crea_opcion_menu("Inicio", "layout-dashboard", caja)
        self.btn_clientes = self.crea_opcion_menu("Clientes", "users", caja)
        self.btn_productos = self.crea_opcion_menu("Productos", "package", caja)
        self.btn_venta = self.crea_opcion_menu("Nueva venta", "shopping-cart", caja)
        self.btn_ventas = self.crea_opcion_menu("Historial de ventas", "receipt", caja)
        self.btn_reportes = self.crea_opcion_menu("Reportes", "chart-column", caja)
        self.btn_usuarios = self.crea_opcion_menu("Usuarios", "user-cog", caja)
        caja.addStretch()
        linea = QFrame()
        linea.setObjectName("linea_menu")
        linea.setFixedHeight(1)
        caja.addWidget(linea)
        caja.addSpacing(10)
        sesion = QHBoxLayout()
        sesion.setSpacing(10)
        self.lbl_avatar = QLabel()
        self.lbl_avatar.setObjectName("avatar")
        self.lbl_avatar.setFixedSize(34, 34)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        datos = QVBoxLayout()
        datos.setSpacing(0)
        self.lbl_sesion_nombre = QLabel()
        self.lbl_sesion_nombre.setObjectName("sesion_nombre")
        self.lbl_sesion_rol = QLabel()
        self.lbl_sesion_rol.setObjectName("sesion_rol")
        datos.addWidget(self.lbl_sesion_nombre)
        datos.addWidget(self.lbl_sesion_rol)
        self.datos_sesion = QWidget()
        self.datos_sesion.setLayout(datos)
        sesion.addWidget(self.lbl_avatar)
        sesion.addWidget(self.datos_sesion, 1)
        caja.addLayout(sesion)
        caja.addSpacing(8)
        self.btn_tema = self.crea_opcion_menu("Modo oscuro", "moon", caja, marcable=False)
        con_tema(self.btn_tema, self.actualiza_boton_tema)
        self.btn_cambiar_clave = self.crea_opcion_menu("Cambiar contraseña", "key-round", caja, marcable=False)
        self.btn_respaldo = self.crea_opcion_menu("Respaldar datos", "database-backup", caja, marcable=False)
        self.btn_cerrar_sesion = self.crea_opcion_menu("Cerrar sesión", "log-out", caja, marcable=False)
        return menu
    def crea_opcion_menu(self, texto, nombre_icono, caja, marcable=True):
        boton = QPushButton(texto)
        boton.texto_menu = texto # AL CONTRAER EL MENU QUEDA SOLO EL ICONO Y EL NOMBRE PASA AL TOOLTIP
        boton.nombre_icono = nombre_icono
        con_tema(boton, lambda: boton.setIcon(icono(boton.nombre_icono, TEMA["menu_texto"], "#ffffff")))
        boton.setIconSize(QSize(18, 18))
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        if marcable:
            boton.setCheckable(True)
            self.grupo_menu.addButton(boton)
        caja.addWidget(boton)
        self.opciones_menu.append(boton)
        return boton
    def crea_boton_menu(self, nombre_icono, ayuda): # BOTON DE SOLO ICONO DENTRO DEL MENU
        boton = QPushButton()
        boton.setProperty("tipo", "icono_menu")
        boton.setFixedSize(32, 32)
        boton.setIconSize(QSize(18, 18))
        boton.setToolTip(ayuda)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        boton.nombre_icono = nombre_icono
        con_tema(boton, lambda: boton.setIcon(icono(boton.nombre_icono, TEMA["menu_texto"])))
        return boton
    def actualiza_boton_tema(self): # LUNA EN MODO CLARO, SOL EN MODO OSCURO
        boton = self.btn_tema
        boton.nombre_icono = "sun" if tema_actual == "oscuro" else "moon"
        boton.texto_menu = "Modo claro" if tema_actual == "oscuro" else "Modo oscuro"
        boton.setIcon(icono(boton.nombre_icono, TEMA["menu_texto"], "#ffffff"))
        if self.menu_contraido:
            boton.setToolTip(boton.texto_menu)
        else:
            boton.setText(boton.texto_menu)
    def contrae_menu(self, contraido, animado=True): # MENU ANGOSTO CON SOLO ICONOS: MAS ESPACIO PARA LAS TABLAS
        if contraido == self.menu_contraido:
            return
        self.menu_contraido = contraido
        for boton in self.opciones_menu:
            if contraido:
                boton.atajo_menu = boton.toolTip()
                boton.setText("")
                boton.setToolTip(boton.texto_menu + (f" ({boton.atajo_menu})" if boton.atajo_menu else ""))
            else:
                boton.setText(boton.texto_menu)
                boton.setToolTip(getattr(boton, "atajo_menu", boton.toolTip()))
        for widget in (self.lbl_marca, self.lbl_seccion_menu, self.datos_sesion):
            widget.setVisible(not contraido)
        self.btn_contraer.nombre_icono = "panel-left-open" if contraido else "panel-left-close"
        self.btn_contraer.setIcon(icono(self.btn_contraer.nombre_icono, TEMA["menu_texto"]))
        self.btn_contraer.setToolTip("Expandir menú" if contraido else "Contraer menú")
        ancho = self.ANCHO_MENU_CONTRAIDO if contraido else self.ANCHO_MENU
        if getattr(self, "animacion_menu", None) is not None:
            self.animacion_menu.stop() # SI NO, LA ANIMACION ANTERIOR SEGUIRIA CAMBIANDO EL ANCHO
        if not animado or not ANIMACIONES:
            self.menu.setFixedWidth(ancho)
            return
        self.animacion_menu = QParallelAnimationGroup(self.menu)
        for propiedad in (b"minimumWidth", b"maximumWidth"):
            animacion = QPropertyAnimation(self.menu, propiedad)
            animacion.setDuration(180)
            animacion.setStartValue(self.menu.width())
            animacion.setEndValue(ancho)
            animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animacion_menu.addAnimation(animacion)
        self.animacion_menu.start()
    def cambia_pagina(self, pagina): # LA PANTALLA NUEVA APARECE CON UN FUNDIDO BREVE
        if self.paginas.currentWidget() is pagina:
            return
        if self.animacion_pagina is not None: # SI LA ANTERIOR NO TERMINO, SE COMPLETA YA
            self.animacion_pagina.stop()
            self.termina_fundido()
        self.paginas.setCurrentWidget(pagina)
        if not ANIMACIONES:
            return
        efecto = QGraphicsOpacityEffect(pagina)
        pagina.setGraphicsEffect(efecto)
        self.animacion_pagina = QPropertyAnimation(efecto, b"opacity", pagina)
        self.animacion_pagina.setDuration(160)
        self.animacion_pagina.setStartValue(0.0)
        self.animacion_pagina.setEndValue(1.0)
        self.animacion_pagina.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animacion_pagina.finished.connect(self.termina_fundido)
        self.pagina_animada = pagina
        self.animacion_pagina.start()
    def termina_fundido(self): # SIN EFECTO AL TERMINAR: LAS TABLAS SE DIBUJAN DIRECTO (MAS RAPIDO)
        if self.animacion_pagina is not None and not sip.isdeleted(self.pagina_animada):
            self.pagina_animada.setGraphicsEffect(None)
        self.animacion_pagina = None
    def bloquea_pantalla(self, nombre, usuario, iniciales): # NADA DE LO QUE HAY DETRAS SE VE NI SE PUEDE USAR
        self.notificacion.hide()
        self.menu.setEnabled(False)
        self.paginas.setEnabled(False)
        self.bloqueo.muestra(nombre, usuario, iniciales)
    def desbloquea_pantalla(self):
        self.bloqueo.hide()
        self.menu.setEnabled(True)
        self.paginas.setEnabled(True)
    def bloqueada(self):
        return not self.bloqueo.isHidden()

    def crea_pagina(self, titulo, subtitulo):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        cabecera = QHBoxLayout()
        cabecera.addLayout(crea_titulo(titulo, subtitulo))
        cabecera.addStretch()
        layout.addLayout(cabecera)
        return pagina, layout, cabecera

    def crea_inicio(self): # PANEL CON LOS INDICADORES DEL NEGOCIO
        pagina, layout, cabecera = self.crea_pagina("-", "-") # EL SALUDO Y LA FECHA SE COMPLETAN AL ABRIR
        titulos = cabecera.itemAt(0).layout()
        self.lbl_saludo = titulos.itemAt(0).widget()
        self.lbl_fecha_hoy = titulos.itemAt(1).widget()
        tarjetas = QGridLayout()
        tarjetas.setSpacing(16)
        self.tarjeta_hoy = Indicador("Ventas de hoy", "banknote")
        self.tarjeta_mes = Indicador("Ventas del mes", "calendar-days")
        self.tarjeta_clientes = Indicador("Clientes", "users")
        self.tarjeta_stock = Indicador("Stock bajo", "triangle-alert")
        for columna, tarjeta in enumerate((self.tarjeta_hoy, self.tarjeta_mes, self.tarjeta_clientes, self.tarjeta_stock)):
            tarjetas.addWidget(tarjeta, 0, columna)
            tarjetas.setColumnStretch(columna, 1)
        layout.addLayout(tarjetas)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(20)
        # IZQUIERDA: VENTAS POR DIA (UNA SOLA SERIE: EL TITULO LA NOMBRA, SIN LEYENDA)
        self.grupo_grafico = Tarjeta("Ventas por día")
        self.grupo_dias = QButtonGroup(pagina)
        self.btn_7_dias = crea_boton("7 días")
        self.btn_30_dias = crea_boton("30 días")
        for boton, lado in ((self.btn_7_dias, "izquierdo"), (self.btn_30_dias, "derecho")):
            boton.setProperty("tipo", "segmento")
            boton.setProperty("lado", lado)
            boton.setCheckable(True)
            self.grupo_dias.addButton(boton)
        self.btn_7_dias.setChecked(True)
        self.grupo_grafico.cabecera.setSpacing(0)
        self.grupo_grafico.cabecera.addWidget(self.btn_7_dias)
        self.grupo_grafico.cabecera.addWidget(self.btn_30_dias)
        self.lbl_resumen_grafico = QLabel()
        self.lbl_resumen_grafico.setObjectName("tenue")
        self.grafico_inicio = GraficoBarras("Sin ventas en estos días.")
        self.grupo_grafico.addWidget(self.lbl_resumen_grafico)
        self.grupo_grafico.addWidget(self.grafico_inicio, 1)
        cuerpo.addWidget(self.grupo_grafico, 3)
        # DERECHA: RANKING DEL MES Y STOCK BAJO
        derecha = QVBoxLayout()
        derecha.setSpacing(20)
        grupo = Tarjeta("Más vendidos del mes")
        self.lista_mas_vendidos = ListaRanking("Aún no hay ventas este mes.")
        grupo.addWidget(self.lista_mas_vendidos, 1)
        derecha.addWidget(grupo) # ALTO JUSTO PARA 5 FILAS; EL RESTO ES PARA EL STOCK BAJO
        grupo = Tarjeta("Stock bajo (5 unidades o menos)")
        self.tabla_stock_bajo = Tabla(["Producto", "Stock"], 0, "Todo el stock está en orden.", derecha=(1,))
        self.tabla_stock_bajo.verticalHeader().setDefaultSectionSize(36)
        grupo.addWidget(self.tabla_stock_bajo, 1)
        derecha.addWidget(grupo, 1)
        cuerpo.addLayout(derecha, 2)
        layout.addLayout(cuerpo, 1)
        return pagina

    def crea_compras_cliente(self): # RESUMEN DE LO QUE COMPRO EL CLIENTE ELEGIDO
        self.grupo_compras = Tarjeta("Compras del cliente")
        cifras = QGridLayout()
        cifras.setHorizontalSpacing(16)
        cifras.setVerticalSpacing(2)
        self.lbl_total_gastado, self.lbl_num_compras, self.lbl_ultima_compra = QLabel(), QLabel(), QLabel()
        for columna, (titulo, valor) in enumerate((("Total gastado", self.lbl_total_gastado), ("Compras", self.lbl_num_compras),
                                                   ("Última compra", self.lbl_ultima_compra))):
            valor.setObjectName("cifra")
            etiqueta = QLabel(titulo)
            etiqueta.setObjectName("tenue")
            cifras.addWidget(valor, 0, columna)
            cifras.addWidget(etiqueta, 1, columna)
            cifras.setColumnStretch(columna, 1)
        self.lbl_sin_compras = QLabel()
        self.lbl_sin_compras.setObjectName("vacio_texto")
        self.lbl_sin_compras.setWordWrap(True)
        self.btn_ver_compras = crea_boton("Ver en el historial", nombre_icono="receipt")
        self.caja_cifras = QWidget()
        self.caja_cifras.setLayout(cifras)
        self.grupo_compras.cabecera.addWidget(self.btn_ver_compras)
        self.grupo_compras.addWidget(self.caja_cifras)
        self.grupo_compras.addWidget(self.lbl_sin_compras)
        return self.grupo_compras

    def crea_codigo(self):
        campo = QLineEdit()
        campo.setReadOnly(True) # LO ASIGNA LA BASE DE DATOS
        return campo
    def crea_stock(self):
        campo = QSpinBox()
        campo.setRange(0, 1000000)
        campo.setSuffix(" unid.")
        return campo

    def crea_venta(self):
        pagina, layout, _ = self.crea_pagina("Nueva venta", "Elige el cliente, agrega productos y registra la venta.")
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(20)
        # IZQUIERDA: CLIENTE Y PRODUCTOS
        izquierda = QVBoxLayout()
        izquierda.setSpacing(20)
        grupo_cliente = Tarjeta("1. Cliente")
        self.btn_cliente_varios = crea_boton("Cliente varios", nombre_icono="user-round")
        self.btn_cliente_varios.setToolTip("Venta rápida sin registrar al comprador (solo al contado)")
        self.btn_nuevo_cliente = crea_boton("Nuevo cliente", nombre_icono="user-plus")
        self.btn_nuevo_cliente.setToolTip("Registrar un cliente sin salir de la venta")
        grupo_cliente.cabecera.addWidget(self.btn_cliente_varios)
        grupo_cliente.cabecera.addWidget(self.btn_nuevo_cliente)
        self.buscador_cliente_venta = crea_buscador("Buscar cliente por código, nombre o DNI")
        self.tabla_clientes_venta = Tabla(["Código", "Nombre", "DNI"], 1, derecha=(0,), ordenable=True)
        self.tabla_clientes_venta.setMinimumHeight(130) # AL MENOS 3 CLIENTES VISIBLES
        grupo_cliente.addWidget(self.buscador_cliente_venta)
        grupo_cliente.addWidget(self.tabla_clientes_venta, 1)
        grupo_producto = Tarjeta("2. Productos")
        self.buscador_producto_venta = crea_buscador("Buscar o escanear el código del producto (Enter lo agrega)")
        self.tabla_productos_venta = Tabla(["Código", "Producto", "Marca", "Precio", "Stock"], 1, derecha=(0, 3, 4), ordenable=True)
        fila = QHBoxLayout()
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1)
        self.spn_cantidad.setMinimumWidth(90)
        self.lbl_disponible = QLabel()
        self.lbl_disponible.setObjectName("tenue")
        self.btn_agregar = crea_boton("Agregar", "primario", "plus")
        etiqueta = QLabel("Cantidad")
        etiqueta.setObjectName("etiqueta_campo")
        fila.addWidget(etiqueta)
        fila.addWidget(self.spn_cantidad)
        fila.addWidget(self.lbl_disponible)
        fila.addStretch()
        fila.addWidget(self.btn_agregar)
        grupo_producto.addWidget(self.buscador_producto_venta)
        grupo_producto.addWidget(self.tabla_productos_venta, 1)
        grupo_producto.addLayout(fila)
        izquierda.addWidget(grupo_cliente, 2)
        izquierda.addWidget(grupo_producto, 3)
        # DERECHA: EL TICKET DE LA VENTA
        ticket = Tarjeta("3. Detalle de la venta")
        self.lbl_num_venta = QLabel()
        self.lbl_num_venta.setObjectName("tenue")
        ticket.cabecera.addWidget(self.lbl_num_venta)
        self.chip_cliente = QFrame()
        self.chip_cliente.setObjectName("chip")
        chip = QHBoxLayout(self.chip_cliente)
        chip.setContentsMargins(10, 8, 10, 8)
        chip.setSpacing(10)
        self.lbl_iniciales_cliente = QLabel()
        self.lbl_iniciales_cliente.setObjectName("iniciales")
        self.lbl_iniciales_cliente.setFixedSize(34, 34)
        self.lbl_iniciales_cliente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cliente_venta = QLabel()
        chip.addWidget(self.lbl_iniciales_cliente)
        chip.addWidget(self.lbl_cliente_venta, 1)
        ticket.addWidget(self.chip_cliente)
        ticket.addWidget(crea_separador())
        self.detalle_venta = DetalleVenta("Agrega productos desde la lista de la izquierda.")
        ticket.addWidget(self.detalle_venta, 1)
        ticket.addWidget(crea_separador())
        total = QHBoxLayout()
        etiqueta = QLabel("TOTAL")
        etiqueta.setObjectName("etiqueta_total")
        self.lbl_total = QLabel()
        self.lbl_total.setObjectName("monto_ticket")
        total.addWidget(etiqueta, 0, Qt.AlignmentFlag.AlignVCenter)
        total.addStretch()
        total.addWidget(self.lbl_total)
        ticket.addLayout(total)
        pago = QHBoxLayout()
        pago.setSpacing(0)
        etiqueta = QLabel("Forma de pago")
        etiqueta.setObjectName("etiqueta_campo")
        self.grupo_pago = QButtonGroup(pagina)
        self.btn_contado = crea_boton("Contado")
        self.btn_credito = crea_boton("Crédito")
        for boton, lado in ((self.btn_contado, "izquierdo"), (self.btn_credito, "derecho")):
            boton.setProperty("tipo", "segmento")
            boton.setProperty("lado", lado)
            boton.setCheckable(True)
            self.grupo_pago.addButton(boton)
        self.btn_contado.setChecked(True)
        pago.addWidget(etiqueta)
        pago.addSpacing(12)
        pago.addWidget(self.btn_contado)
        pago.addWidget(self.btn_credito)
        pago.addStretch()
        ticket.addLayout(pago)
        self.caja_recibido = QWidget() # SOLO AL CONTADO: CUANTO ENTREGO EL CLIENTE Y SU VUELTO
        recibido = QHBoxLayout(self.caja_recibido)
        recibido.setContentsMargins(0, 0, 0, 0)
        etiqueta = QLabel("Recibido (S/)")
        etiqueta.setObjectName("etiqueta_campo")
        self.txt_recibido = crea_texto("0.00", 12, patron=r"\d{0,8}([.,]\d{0,2})?")
        self.txt_recibido.setFixedWidth(130)
        self.lbl_vuelto = QLabel()
        self.lbl_vuelto.setObjectName("vuelto")
        recibido.addWidget(etiqueta)
        recibido.addSpacing(12)
        recibido.addWidget(self.txt_recibido)
        recibido.addStretch()
        recibido.addWidget(self.lbl_vuelto)
        ticket.addWidget(self.caja_recibido)
        self.btn_registrar_venta = crea_boton("Registrar venta", "primario", "circle-check", grande=True)
        self.btn_cancelar_venta = crea_boton("Cancelar venta")
        self.btn_cancelar_venta.setProperty("tipo", "enlace")
        ticket.addWidget(self.btn_registrar_venta)
        ticket.addWidget(self.btn_cancelar_venta)
        cuerpo.addLayout(izquierda, 4)
        cuerpo.addWidget(ticket, 3)
        layout.addLayout(cuerpo, 1)
        return pagina

    def crea_historial(self): # VENTAS REGISTRADAS: DETALLE, BOLETA Y ANULACION
        pagina, layout, _ = self.crea_pagina("Historial de ventas", "Consulta ventas anteriores, genera su boleta o anúlalas.")
        filtros = QHBoxLayout()
        filtros.setSpacing(12)
        self.periodo_ventas = SelectorPeriodo("Este mes")
        self.fecha_desde, self.fecha_hasta = self.periodo_ventas.desde, self.periodo_ventas.hasta
        self.cmb_estado_venta = crea_combo([("Todas", None), ("Registradas", "REGISTRADA"), ("Anuladas", "ANULADA")])
        self.buscador_ventas = crea_buscador("N° de venta, cliente o DNI")
        filtros.addWidget(self.periodo_ventas)
        filtros.addLayout(con_etiqueta("Estado", self.cmb_estado_venta))
        filtros.addLayout(con_etiqueta("Buscar", self.buscador_ventas), 1)
        layout.addLayout(filtros)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(20)
        lista = Tarjeta()
        self.tabla_ventas = Tabla(["N°", "Fecha", "Cliente", "Total", "Estado"], 2, "No hay ventas con estos filtros.", derecha=(0, 3), ordenable=True)
        self.lbl_resumen_ventas = QLabel()
        self.lbl_resumen_ventas.setObjectName("tenue")
        lista.addWidget(self.tabla_ventas, 1)
        lista.addWidget(self.lbl_resumen_ventas)
        self.grupo_detalle_venta = Tarjeta("Detalle") # SE VE COMO EL TICKET DE LA VENTA, PERO DE SOLO LECTURA
        self.lbl_fecha_detalle = QLabel()
        self.lbl_fecha_detalle.setObjectName("tenue")
        self.grupo_detalle_venta.cabecera.addWidget(self.lbl_fecha_detalle)
        self.lbl_info_venta = QLabel()
        self.lbl_info_venta.setWordWrap(True)
        self.sello_anulada = QFrame() # AVISO VISIBLE DE VENTA ANULADA, CON QUIEN, CUANDO Y POR QUE
        self.sello_anulada.setObjectName("sello")
        sello = QHBoxLayout(self.sello_anulada)
        sello.setContentsMargins(12, 10, 12, 10)
        sello.setSpacing(10)
        icono_sello = QLabel()
        pon_pixmap(icono_sello, "ban", "peligro", 20)
        textos_sello = QVBoxLayout()
        textos_sello.setSpacing(2)
        titulo_sello = QLabel("VENTA ANULADA")
        titulo_sello.setObjectName("titulo_sello")
        self.lbl_sello = QLabel()
        self.lbl_sello.setWordWrap(True)
        self.lbl_sello.setTextFormat(Qt.TextFormat.PlainText) # EL MOTIVO LO ESCRIBE UN USUARIO: NO SE INTERPRETA COMO HTML
        textos_sello.addWidget(titulo_sello)
        textos_sello.addWidget(self.lbl_sello)
        sello.addWidget(icono_sello, 0, Qt.AlignmentFlag.AlignTop)
        sello.addLayout(textos_sello, 1)
        self.sello_anulada.hide()
        self.detalle_historial = DetalleVenta("Selecciona una venta para ver su detalle.", "receipt")
        total = QHBoxLayout()
        self.lbl_etiqueta_total_venta = QLabel("TOTAL")
        self.lbl_etiqueta_total_venta.setObjectName("etiqueta_total")
        self.lbl_total_venta = QLabel()
        self.lbl_total_venta.setObjectName("monto_ticket")
        total.addWidget(self.lbl_etiqueta_total_venta, 0, Qt.AlignmentFlag.AlignVCenter)
        total.addStretch()
        total.addWidget(self.lbl_total_venta)
        botones = QHBoxLayout()
        self.btn_anular = crea_boton("Anular venta", "peligro", "ban")
        self.btn_imprimir = crea_boton("Imprimir", nombre_icono="printer")
        self.btn_boleta = crea_boton("Boleta PDF…", "primario", "file-text")
        botones.addWidget(self.btn_anular)
        botones.addStretch()
        botones.addWidget(self.btn_imprimir)
        botones.addWidget(self.btn_boleta)
        self.grupo_detalle_venta.addWidget(self.lbl_info_venta)
        self.grupo_detalle_venta.addWidget(self.sello_anulada)
        self.separadores_detalle = [crea_separador(), crea_separador()]
        self.grupo_detalle_venta.addWidget(self.separadores_detalle[0])
        self.grupo_detalle_venta.addWidget(self.detalle_historial, 1)
        self.grupo_detalle_venta.addWidget(self.separadores_detalle[1])
        self.grupo_detalle_venta.addLayout(total)
        self.grupo_detalle_venta.addLayout(botones)
        cuerpo.addWidget(lista, 3)
        cuerpo.addWidget(self.grupo_detalle_venta, 2)
        layout.addLayout(cuerpo, 1)
        return pagina

    def crea_reportes(self):
        pagina, layout, cabecera = self.crea_pagina("Reportes de ventas", "Elige el periodo: el reporte se actualiza solo.")
        self.btn_exportar_excel = crea_boton("Exportar a Excel…", nombre_icono="sheet")
        self.btn_exportar_pdf = crea_boton("Exportar a PDF…", "primario", "file-down")
        cabecera.addWidget(self.btn_exportar_excel, 0, Qt.AlignmentFlag.AlignBottom)
        cabecera.addWidget(self.btn_exportar_pdf, 0, Qt.AlignmentFlag.AlignBottom)
        filtros = QHBoxLayout()
        filtros.setSpacing(12)
        self.periodo_reporte = SelectorPeriodo("Este mes")
        self.cmb_agrupar = crea_combo([("Ventas (una fila por venta)", "ventas"), ("Productos", "productos"), ("Vendedores", "vendedores")])
        filtros.addWidget(self.periodo_reporte)
        filtros.addLayout(con_etiqueta("Agrupar por", self.cmb_agrupar))
        filtros.addStretch()
        layout.addLayout(filtros)
        arriba = QHBoxLayout()
        arriba.setSpacing(20)
        cifras = QVBoxLayout() # CIFRAS CLAVE DEL PERIODO
        cifras.setSpacing(12)
        self.cifras_reporte = cifras
        self.cifra_ventas = Indicador("N° de ventas", "receipt")
        self.cifra_total = Indicador("Total vendido", "banknote")
        self.cifra_promedio = Indicador("Ticket promedio", "wallet")
        for cifra in (self.cifra_ventas, self.cifra_total, self.cifra_promedio):
            cifra.layout().setContentsMargins(16, 10, 16, 10)
            cifra.detalle.hide()
            cifras.addWidget(cifra)
        arriba.addLayout(cifras, 1)
        self.grupo_grafico_reporte = Tarjeta("Ventas por día")
        self.grafico_reporte = GraficoBarras()
        self.grafico_reporte.setMinimumHeight(170)
        self.grupo_grafico_reporte.addWidget(self.grafico_reporte, 1)
        arriba.addWidget(self.grupo_grafico_reporte, 3)
        self.caja_resumen_reporte = QWidget()
        self.caja_resumen_reporte.setLayout(arriba)
        layout.addWidget(self.caja_resumen_reporte)
        resultado = Tarjeta()
        self.lbl_periodo = QLabel()
        self.lbl_periodo.setObjectName("titulo_tarjeta")
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setObjectName("tenue")
        resultado.cabecera.insertWidget(0, self.lbl_periodo)
        resultado.cabecera.addWidget(self.lbl_resumen)
        self.tabla_reporte = Tabla(["N° venta", "Fecha", "Productos", "Cliente", "Pago", "Total"], 2, derecha=(0, 5), ordenable=True)
        resultado.addWidget(self.tabla_reporte, 1)
        layout.addWidget(resultado, 1)
        return pagina
    def muestra_grafico_reporte(self, visible): # SIN GRAFICO (UN SOLO DIA) LAS CIFRAS VAN EN UNA FILA
        self.grupo_grafico_reporte.setVisible(visible)
        self.cifras_reporte.setDirection(QBoxLayout.Direction.TopToBottom if visible else QBoxLayout.Direction.LeftToRight)

def prepara_aplicacion(app, tema="claro"): # FUENTES, TEMA ELEGIDO (NO EL DEL SISTEMA), ESTILO E ICONO
    carga_fuentes()
    app.setStyle("Fusion") # SE VE IGUAL EN WINDOWS, LINUX Y MAC
    fuente = QFont("Inter", 10)
    fuente.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(fuente)
    aplica_tema(app, tema)
    app.setWindowIcon(icono_aplicacion())
