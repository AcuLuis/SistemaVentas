# INTERFAZ CONSTRUIDA CON LAYOUTS: SE ADAPTA AL TAMAÑO DE LA VENTANA Y AL ZOOM DE LA PANTALLA
import os
from PyQt6.QtCore import Qt, QRegularExpression, QDate
from PyQt6.QtGui import QPixmap, QRegularExpressionValidator
from PyQt6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QTableWidget,
                             QHeaderView, QAbstractItemView, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox,
                             QStackedWidget, QButtonGroup, QCheckBox, QDateEdit, QDialog, QGridLayout)

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
COLOR_PRIMARIO = "#147186" # EL TURQUESA DE LOS BOTONES ORIGINALES
COLOR_PELIGRO = "#b42318"
# QSS USA "/" EN LAS RUTAS, TAMBIEN EN WINDOWS
FLECHA_ARRIBA = os.path.join(DIRECTORIO, "iconos", "flecha_arriba.svg").replace("\\", "/")
FLECHA_ABAJO = os.path.join(DIRECTORIO, "iconos", "flecha_abajo.svg").replace("\\", "/")
ESTILO = f"""
QMainWindow, QDialog, QStackedWidget > QWidget {{ background: #f4f5f7; }}
QWidget {{ color: #1f2329; font-size: 10pt; }}
QFrame#menu {{ background: #1f2329; }}
QFrame#menu QLabel {{ color: #ffffff; }}
QLabel#marca {{ font-size: 13pt; font-weight: bold; padding: 6px 4px 18px 4px; }}
QFrame#menu QLabel#sesion {{ color: #c9ced6; font-size: 9pt; padding: 4px; }}
QFrame#menu QPushButton {{ color: #e8eaed; background: transparent; border: none; text-align: left; padding: 10px 14px; border-radius: 6px; }}
QFrame#menu QPushButton:hover {{ background: #2d333b; }}
QFrame#menu QPushButton:checked {{ background: {COLOR_PRIMARIO}; color: #ffffff; font-weight: bold; }}
QFrame#menu QPushButton[tipo="pie"] {{ color: #c9ced6; padding: 6px 14px; font-size: 9pt; }}
QLabel#titulo {{ font-size: 17pt; font-weight: bold; }}
QLabel#subtitulo {{ color: #5f6773; }}
QLabel#total {{ font-size: 16pt; font-weight: bold; color: {COLOR_PRIMARIO}; }}
QLabel#error {{ color: {COLOR_PELIGRO}; }}
QFrame#tarjeta {{ background: #ffffff; border: 1px solid #d0d4da; border-radius: 8px; }}
QFrame#tarjeta QLabel {{ border: none; }}
QLabel#valor_tarjeta {{ font-size: 18pt; font-weight: bold; color: {COLOR_PRIMARIO}; }}
QGroupBox {{ background: #ffffff; border: 1px solid #d0d4da; border-radius: 8px; margin-top: 16px; padding: 12px 10px 10px 10px; font-weight: bold; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
QGroupBox QLabel, QGroupBox QCheckBox {{ font-weight: normal; }}
QLineEdit, QComboBox, QSpinBox, QDateEdit {{ background: #ffffff; border: 1px solid #c3c8cf; border-radius: 4px; padding: 4px 6px; min-height: 22px; font-weight: normal; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{ border: 1px solid {COLOR_PRIMARIO}; }}
QLineEdit:read-only {{ background: #eceef1; color: #5f6773; }}
QSpinBox {{ padding-right: 24px; }}
QSpinBox::up-button, QSpinBox::down-button {{ subcontrol-origin: border; width: 22px; background: #f4f5f7; border-left: 1px solid #c3c8cf; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-bottom: 1px solid #c3c8cf; border-top-right-radius: 4px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 4px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #e3e6ea; }}
QSpinBox::up-arrow {{ image: url("{FLECHA_ARRIBA}"); width: 10px; height: 6px; }}
QSpinBox::down-arrow, QComboBox::down-arrow, QDateEdit::down-arrow {{ image: url("{FLECHA_ABAJO}"); width: 10px; height: 6px; }}
QComboBox, QDateEdit {{ padding-right: 26px; }}
QComboBox::drop-down, QDateEdit::drop-down {{ subcontrol-origin: border; subcontrol-position: center right; width: 24px; border-left: 1px solid #c3c8cf; }}
QComboBox QAbstractItemView {{ background: #ffffff; selection-background-color: #cfe6ec; selection-color: #1f2329; }}
QPushButton {{ background: #ffffff; border: 1px solid #c3c8cf; border-radius: 4px; padding: 6px 14px; font-weight: normal; }}
QPushButton:hover {{ background: #eef1f4; }}
QPushButton[tipo="primario"] {{ background: {COLOR_PRIMARIO}; color: #ffffff; border: none; font-weight: bold; }}
QPushButton[tipo="primario"]:hover {{ background: #0f5a6b; }}
QPushButton[tipo="peligro"] {{ background: #ffffff; color: {COLOR_PELIGRO}; border: 1px solid {COLOR_PELIGRO}; }}
QPushButton[tipo="peligro"]:hover {{ background: #fdecea; }}
QPushButton:disabled, QPushButton[tipo="primario"]:disabled, QPushButton[tipo="peligro"]:disabled {{ background: #e3e6ea; color: #8a929c; border: none; }}
QTableWidget {{ background: #ffffff; alternate-background-color: #f7f8fa; border: 1px solid #d0d4da; gridline-color: #e6e8eb;
               selection-background-color: #cfe6ec; selection-color: #1f2329; font-weight: normal; }}
QHeaderView::section {{ background: #e9ecef; padding: 6px; border: none; border-right: 1px solid #d0d4da; font-weight: bold; }}
QStatusBar {{ background: #ffffff; border-top: 1px solid #d0d4da; }}
"""

# AYUDANTES
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
def crea_boton(texto, tipo=None):
    boton = QPushButton(texto)
    if tipo:
        boton.setProperty("tipo", tipo)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    return boton
def crea_buscador(texto):
    buscador = QLineEdit()
    buscador.setPlaceholderText(texto)
    buscador.setClearButtonEnabled(True)
    return buscador
def crea_tabla(encabezados, columna_ancha):
    tabla = QTableWidget(0, len(encabezados))
    tabla.setHorizontalHeaderLabels(encabezados)
    tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # SOLO LECTURA: SE EDITA EN EL FORMULARIO
    tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tabla.setAlternatingRowColors(True)
    tabla.verticalHeader().setVisible(False)
    encabezado = tabla.horizontalHeader()
    encabezado.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    encabezado.setSectionResizeMode(columna_ancha, QHeaderView.ResizeMode.Stretch) # ESTA COLUMNA OCUPA EL ESPACIO LIBRE
    return tabla
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
def crea_logo(ancho, alto):
    logo = QLabel()
    logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    imagen = QPixmap(os.path.join(DIRECTORIO, "inicio_logo.jpg"))
    if not imagen.isNull():
        logo.setPixmap(imagen.scaled(ancho, alto, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    return logo

class Tarjeta(QFrame): # INDICADOR DEL PANEL DE INICIO
    def __init__(self, titulo):
        super().__init__()
        self.setObjectName("tarjeta")
        caja = QVBoxLayout(self)
        caja.setContentsMargins(16, 12, 16, 12)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("subtitulo")
        self.valor = QLabel("-")
        self.valor.setObjectName("valor_tarjeta")
        self.detalle = QLabel()
        self.detalle.setObjectName("subtitulo")
        caja.addWidget(etiqueta)
        caja.addWidget(self.valor)
        caja.addWidget(self.detalle)

class PaginaCrud(QWidget): # TABLA CON BUSCADOR A LA IZQUIERDA Y FORMULARIO A LA DERECHA
    def __init__(self, titulo, subtitulo, encabezados, columna_ancha, texto_busqueda, campos):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.addLayout(crea_titulo(titulo, subtitulo))
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(16)
        izquierda = QVBoxLayout()
        self.buscador = crea_buscador(texto_busqueda)
        self.tabla = crea_tabla(encabezados, columna_ancha)
        self.lbl_conteo = QLabel()
        self.lbl_conteo.setObjectName("subtitulo")
        izquierda.addWidget(self.buscador)
        izquierda.addWidget(self.tabla)
        izquierda.addWidget(self.lbl_conteo)
        self.grupo = QGroupBox()
        formulario = QFormLayout(self.grupo)
        formulario.setVerticalSpacing(10)
        self.campos = {}
        for clave, etiqueta, widget in campos:
            formulario.addRow(etiqueta, widget)
            self.campos[clave] = widget
        self.btn_nuevo = crea_boton("Nuevo")
        self.btn_guardar = crea_boton("Guardar", "primario")
        self.btn_eliminar = crea_boton("Eliminar", "peligro")
        botones = QHBoxLayout()
        botones.addWidget(self.btn_eliminar)
        botones.addStretch()
        botones.addWidget(self.btn_nuevo)
        botones.addWidget(self.btn_guardar)
        formulario.addRow(botones)
        derecha = QVBoxLayout()
        derecha.addWidget(self.grupo)
        derecha.addStretch()
        cuerpo.addLayout(izquierda, 3)
        cuerpo.addLayout(derecha, 2)
        layout.addLayout(cuerpo)

class DialogoLogin(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iniciar sesión - Sistema de Ventas")
        self.setFixedWidth(440)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(28, 24, 28, 24)
        caja.setSpacing(10)
        caja.addWidget(crea_logo(384, 192))
        caja.addLayout(crea_titulo("Bienvenido", "Ingresa con tu usuario para continuar."))
        self.txt_usuario = crea_texto("Usuario", 30)
        self.txt_clave = crea_clave()
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("error")
        self.lbl_error.setWordWrap(True)
        self.btn_ingresar = crea_boton("Ingresar", "primario")
        self.btn_ingresar.setDefault(True) # ENTER = INGRESAR
        caja.addWidget(self.txt_usuario)
        caja.addWidget(self.txt_clave)
        caja.addWidget(self.lbl_error)
        caja.addWidget(self.btn_ingresar)

class DialogoClave(QDialog):
    def __init__(self, padre):
        super().__init__(padre)
        self.setWindowTitle("Cambiar contraseña")
        self.setFixedWidth(380)
        caja = QVBoxLayout(self)
        caja.setContentsMargins(24, 20, 24, 20)
        formulario = QFormLayout()
        self.txt_actual = crea_clave("Contraseña actual")
        self.txt_nueva = crea_clave("Mínimo 6 caracteres")
        self.txt_repite = crea_clave("Repite la nueva contraseña")
        formulario.addRow("Actual", self.txt_actual)
        formulario.addRow("Nueva", self.txt_nueva)
        formulario.addRow("Repetir", self.txt_repite)
        self.lbl_error = QLabel()
        self.lbl_error.setObjectName("error")
        self.lbl_error.setWordWrap(True)
        botones = QHBoxLayout()
        self.btn_cancelar = crea_boton("Cancelar")
        self.btn_guardar = crea_boton("Guardar", "primario")
        self.btn_guardar.setDefault(True)
        botones.addStretch()
        botones.addWidget(self.btn_cancelar)
        botones.addWidget(self.btn_guardar)
        caja.addLayout(formulario)
        caja.addWidget(self.lbl_error)
        caja.addLayout(botones)
        self.btn_cancelar.clicked.connect(self.reject)

class Interfaz:
    def __init__(self, ventana):
        ventana.setWindowTitle("Sistema de Ventas")
        ventana.resize(1200, 720)
        ventana.setMinimumSize(1100, 680)
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.crea_menu())
        self.paginas = QStackedWidget()
        self.inicio = self.crea_inicio()
        self.clientes = PaginaCrud("Clientes", "Registra, busca y edita a tus clientes.",
                                   ["Código", "Nombre", "DNI", "Teléfono", "Sexo"], 1, "Buscar por código, nombre o DNI", [
            ("codigo", "Código", self.crea_codigo()),
            ("nombre", "Nombre", crea_texto("Nombre y apellido")),
            ("dni", "DNI", crea_texto("8 dígitos", 8, solo_digitos=8)),
            ("telefono", "Teléfono", crea_texto("9 dígitos", 9, solo_digitos=9)),
            ("sexo", "Sexo", crea_combo([("Selecciona…", None), ("Masculino", "MASCULINO"), ("Femenino", "FEMENINO")])),
        ])
        self.productos = PaginaCrud("Productos", "Administra el catálogo, los precios y el stock.",
                                    ["Código", "Tipo", "Marca", "Precio", "Stock"], 1, "Buscar por código, tipo o marca", [
            ("codigo", "Código", self.crea_codigo()),
            ("tipo", "Tipo", crea_texto("Ej.: Laptop")),
            ("marca", "Marca", crea_texto("Ej.: HP")),
            ("precio", "Precio (S/)", crea_texto("0.00", 12, patron=r"\d{0,8}([.,]\d{0,2})?")),
            ("stock", "Stock", self.crea_stock()),
        ])
        self.usuarios = PaginaCrud("Usuarios", "Cuentas de acceso al sistema y sus permisos.",
                                   ["Código", "Usuario", "Nombre", "Rol", "Activo"], 2, "Buscar por código, usuario o nombre", [
            ("codigo", "Código", self.crea_codigo()),
            ("usuario", "Usuario", crea_texto("Ej.: jperez (sin espacios)", 30, patron=r"[A-Za-z0-9_.]{0,30}")),
            ("nombre", "Nombre", crea_texto("Nombre completo", 100)),
            ("rol", "Rol", crea_combo([("Selecciona…", None), ("Administrador", "ADMIN"), ("Vendedor", "VENDEDOR")])),
            ("activo", "Estado", QCheckBox("Puede ingresar al sistema")),
            ("clave", "Contraseña", crea_clave("Mínimo 6 caracteres")),
        ])
        self.venta = self.crea_venta()
        self.ventas = self.crea_historial()
        self.reportes = self.crea_reportes()
        for pagina in (self.inicio, self.clientes, self.productos, self.venta, self.ventas, self.reportes, self.usuarios):
            self.paginas.addWidget(pagina)
        layout.addWidget(self.paginas, 1)
        ventana.setCentralWidget(central)
        self.barra_estado = ventana.statusBar()

    def crea_menu(self):
        menu = QFrame()
        menu.setObjectName("menu")
        menu.setFixedWidth(210)
        caja = QVBoxLayout(menu)
        caja.setContentsMargins(12, 18, 12, 14)
        caja.setSpacing(4)
        marca = QLabel("LGD Technologies")
        marca.setObjectName("marca")
        caja.addWidget(marca)
        self.grupo_menu = QButtonGroup(menu)
        self.grupo_menu.setExclusive(True)
        self.btn_inicio = self.crea_opcion_menu("Inicio", caja)
        self.btn_clientes = self.crea_opcion_menu("Clientes", caja)
        self.btn_productos = self.crea_opcion_menu("Productos", caja)
        self.btn_venta = self.crea_opcion_menu("Nueva venta", caja)
        self.btn_ventas = self.crea_opcion_menu("Historial de ventas", caja)
        self.btn_reportes = self.crea_opcion_menu("Reportes", caja)
        self.btn_usuarios = self.crea_opcion_menu("Usuarios", caja)
        caja.addStretch()
        self.lbl_sesion = QLabel()
        self.lbl_sesion.setObjectName("sesion")
        self.lbl_sesion.setWordWrap(True)
        self.btn_cambiar_clave = crea_boton("Cambiar contraseña", "pie")
        self.btn_cerrar_sesion = crea_boton("Cerrar sesión", "pie")
        caja.addWidget(self.lbl_sesion)
        caja.addWidget(self.btn_cambiar_clave)
        caja.addWidget(self.btn_cerrar_sesion)
        return menu
    def crea_opcion_menu(self, texto, caja):
        boton = crea_boton(texto)
        boton.setCheckable(True)
        self.grupo_menu.addButton(boton)
        caja.addWidget(boton)
        return boton

    def crea_inicio(self): # PANEL CON LOS INDICADORES DEL NEGOCIO
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)
        self.lbl_saludo = QLabel()
        self.lbl_saludo.setObjectName("titulo")
        self.lbl_fecha_hoy = QLabel()
        self.lbl_fecha_hoy.setObjectName("subtitulo")
        layout.addWidget(self.lbl_saludo)
        layout.addWidget(self.lbl_fecha_hoy)
        tarjetas = QGridLayout()
        tarjetas.setSpacing(14)
        self.tarjeta_hoy = Tarjeta("Ventas de hoy")
        self.tarjeta_mes = Tarjeta("Ventas del mes")
        self.tarjeta_clientes = Tarjeta("Clientes registrados")
        self.tarjeta_stock = Tarjeta("Productos con stock bajo")
        for columna, tarjeta in enumerate((self.tarjeta_hoy, self.tarjeta_mes, self.tarjeta_clientes, self.tarjeta_stock)):
            tarjetas.addWidget(tarjeta, 0, columna)
        layout.addLayout(tarjetas)
        tablas = QHBoxLayout()
        tablas.setSpacing(16)
        grupo = QGroupBox("Más vendidos del mes")
        caja = QVBoxLayout(grupo)
        self.tabla_mas_vendidos = crea_tabla(["Producto", "Unidades", "Importe"], 0)
        caja.addWidget(self.tabla_mas_vendidos)
        tablas.addWidget(grupo, 3)
        grupo = QGroupBox("Stock bajo (5 unidades o menos)")
        caja = QVBoxLayout(grupo)
        self.tabla_stock_bajo = crea_tabla(["Producto", "Stock"], 0)
        caja.addWidget(self.tabla_stock_bajo)
        tablas.addWidget(grupo, 2)
        layout.addLayout(tablas, 1)
        return pagina

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
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(24, 20, 24, 16)
        cabecera = QHBoxLayout()
        cabecera.addLayout(crea_titulo("Nueva venta", "Elige el cliente, agrega productos y registra la venta."))
        cabecera.addStretch()
        self.lbl_num_venta = QLabel()
        self.lbl_num_venta.setObjectName("subtitulo")
        cabecera.addWidget(self.lbl_num_venta, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(cabecera)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(16)
        # IZQUIERDA: CLIENTE Y PRODUCTOS
        izquierda = QVBoxLayout()
        grupo_cliente = QGroupBox("1. Cliente")
        caja = QVBoxLayout(grupo_cliente)
        self.buscador_cliente_venta = crea_buscador("Buscar cliente por código, nombre o DNI")
        self.tabla_clientes_venta = crea_tabla(["Código", "Nombre", "DNI"], 1)
        self.tabla_clientes_venta.setMinimumHeight(130) # AL MENOS 3 CLIENTES VISIBLES
        self.lbl_cliente_venta = QLabel()
        caja.addWidget(self.buscador_cliente_venta)
        caja.addWidget(self.tabla_clientes_venta)
        caja.addWidget(self.lbl_cliente_venta)
        grupo_producto = QGroupBox("2. Productos")
        caja = QVBoxLayout(grupo_producto)
        self.buscador_producto_venta = crea_buscador("Buscar producto por código, tipo o marca")
        self.tabla_productos_venta = crea_tabla(["Código", "Producto", "Marca", "Precio", "Stock"], 1)
        fila = QHBoxLayout()
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 1)
        self.spn_cantidad.setMinimumWidth(80)
        self.lbl_disponible = QLabel()
        self.lbl_disponible.setObjectName("subtitulo")
        self.btn_agregar = crea_boton("Agregar", "primario")
        fila.addWidget(QLabel("Cantidad"))
        fila.addWidget(self.spn_cantidad)
        fila.addWidget(self.lbl_disponible)
        fila.addStretch()
        fila.addWidget(self.btn_agregar)
        caja.addWidget(self.buscador_producto_venta)
        caja.addWidget(self.tabla_productos_venta)
        caja.addLayout(fila)
        izquierda.addWidget(grupo_cliente, 2)
        izquierda.addWidget(grupo_producto, 3)
        # DERECHA: DETALLE Y TOTAL
        grupo_detalle = QGroupBox("3. Detalle de la venta")
        caja = QVBoxLayout(grupo_detalle)
        self.tabla_carrito = crea_tabla(["Producto", "Cantidad", "Precio", "Subtotal"], 0)
        self.btn_quitar = crea_boton("Quitar producto")
        pago = QHBoxLayout()
        self.cmb_forma_pago = QComboBox()
        self.cmb_forma_pago.addItems(["Contado", "Crédito"])
        pago.addWidget(QLabel("Forma de pago"))
        pago.addWidget(self.cmb_forma_pago)
        pago.addStretch()
        self.lbl_total = QLabel()
        self.lbl_total.setObjectName("total")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        acciones = QHBoxLayout()
        self.btn_cancelar_venta = crea_boton("Cancelar venta")
        self.btn_registrar_venta = crea_boton("Registrar venta", "primario")
        acciones.addWidget(self.btn_cancelar_venta)
        acciones.addStretch()
        acciones.addWidget(self.btn_registrar_venta)
        quitar = QHBoxLayout()
        quitar.addStretch()
        quitar.addWidget(self.btn_quitar)
        caja.addWidget(self.tabla_carrito)
        caja.addLayout(quitar)
        caja.addLayout(pago)
        caja.addWidget(self.lbl_total)
        caja.addLayout(acciones)
        cuerpo.addLayout(izquierda, 3)
        cuerpo.addWidget(grupo_detalle, 2)
        layout.addLayout(cuerpo)
        return pagina

    def crea_historial(self): # VENTAS REGISTRADAS: DETALLE, BOLETA Y ANULACION
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.addLayout(crea_titulo("Historial de ventas", "Consulta ventas anteriores, genera su boleta o anúlalas."))
        filtros = QHBoxLayout()
        hoy = QDate.currentDate()
        self.fecha_desde = crea_fecha(QDate(hoy.year(), hoy.month(), 1))
        self.fecha_hasta = crea_fecha(hoy)
        self.cmb_estado_venta = crea_combo([("Todas", None), ("Registradas", "REGISTRADA"), ("Anuladas", "ANULADA")])
        self.buscador_ventas = crea_buscador("N° de venta o cliente")
        for etiqueta, widget in (("Desde", self.fecha_desde), ("Hasta", self.fecha_hasta), ("Estado", self.cmb_estado_venta)):
            filtros.addWidget(QLabel(etiqueta))
            filtros.addWidget(widget)
        filtros.addWidget(self.buscador_ventas, 1)
        layout.addLayout(filtros)
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(16)
        izquierda = QVBoxLayout()
        self.tabla_ventas = crea_tabla(["N°", "Fecha", "Cliente", "Vendedor", "Pago", "Total", "Estado"], 2)
        self.lbl_resumen_ventas = QLabel()
        self.lbl_resumen_ventas.setObjectName("subtitulo")
        izquierda.addWidget(self.tabla_ventas)
        izquierda.addWidget(self.lbl_resumen_ventas)
        self.grupo_detalle_venta = QGroupBox("Detalle")
        caja = QVBoxLayout(self.grupo_detalle_venta)
        self.lbl_info_venta = QLabel()
        self.lbl_info_venta.setWordWrap(True)
        self.tabla_detalle_venta = crea_tabla(["Producto", "Cant.", "P. unit.", "Subtotal"], 0)
        self.lbl_total_venta = QLabel()
        self.lbl_total_venta.setObjectName("total")
        self.lbl_total_venta.setAlignment(Qt.AlignmentFlag.AlignRight)
        botones = QHBoxLayout()
        self.btn_anular = crea_boton("Anular venta", "peligro")
        self.btn_boleta = crea_boton("Boleta PDF…", "primario")
        botones.addWidget(self.btn_anular)
        botones.addStretch()
        botones.addWidget(self.btn_boleta)
        caja.addWidget(self.lbl_info_venta)
        caja.addWidget(self.tabla_detalle_venta)
        caja.addWidget(self.lbl_total_venta)
        caja.addLayout(botones)
        cuerpo.addLayout(izquierda, 3)
        cuerpo.addWidget(self.grupo_detalle_venta, 2)
        layout.addLayout(cuerpo, 1)
        return pagina

    def crea_reportes(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.addLayout(crea_titulo("Reportes de ventas", "Consulta las ventas de un mes o de una semana y expórtalas a PDF o Excel."))
        filtros = QHBoxLayout()
        self.cmb_tipo_reporte = QComboBox()
        self.cmb_tipo_reporte.addItems(["Mensual", "Semanal"])
        self.cmb_anio = QComboBox()
        self.cmb_mes = QComboBox()
        self.cmb_mes.addItems(["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
                               "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        self.cmb_semana = QComboBox()
        self.cmb_semana.addItems(["Semana 1 (días 1 al 7)", "Semana 2 (días 8 al 14)", "Semana 3 (días 15 al 21)",
                                  "Semana 4 (días 22 al 28)", "Semana 5 (día 29 al fin de mes)"])
        self.lbl_semana = QLabel("Semana")
        self.btn_generar_reporte = crea_boton("Generar reporte", "primario")
        for etiqueta, widget in (("Tipo", self.cmb_tipo_reporte), ("Año", self.cmb_anio), ("Mes", self.cmb_mes)):
            filtros.addWidget(QLabel(etiqueta))
            filtros.addWidget(widget)
        filtros.addWidget(self.lbl_semana)
        filtros.addWidget(self.cmb_semana)
        filtros.addStretch()
        filtros.addWidget(self.btn_generar_reporte)
        layout.addLayout(filtros)
        self.lbl_periodo = QLabel()
        self.lbl_periodo.setObjectName("subtitulo")
        layout.addWidget(self.lbl_periodo)
        self.tabla_reporte = crea_tabla(["N° venta", "Fecha", "Productos", "Cliente", "Pago", "Total"], 2)
        layout.addWidget(self.tabla_reporte, 1)
        pie = QHBoxLayout()
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setObjectName("total")
        self.btn_exportar_excel = crea_boton("Exportar a Excel…")
        self.btn_exportar_pdf = crea_boton("Exportar a PDF…", "primario")
        pie.addWidget(self.lbl_resumen)
        pie.addStretch()
        pie.addWidget(self.btn_exportar_excel)
        pie.addWidget(self.btn_exportar_pdf)
        layout.addLayout(pie)
        return pagina
