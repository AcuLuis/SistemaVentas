import sys
import os
import atexit
import logging
import calendar
import tempfile
from decimal import Decimal
from datetime import date, datetime, timedelta
from xml.sax.saxutils import escape
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QInputDialog, QDialog, QCheckBox, QLineEdit, QAbstractSpinBox
from PyQt6.QtGui import QDesktopServices, QShortcut, QKeySequence, QPainter, QPageSize
from PyQt6.QtCore import Qt, QUrl, QStandardPaths, QTimer, QSettings, QObject, QEvent, QSize, QDate
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtPdf import QPdfDocument
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A5
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
import pymysql
import bd
import interfaz
import seguridad

ARCHIVO_LOG = os.path.join(bd.DIRECTORIO_DATOS, "sistema_ventas.log")
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
STOCK_BAJO = 5
MAX_INTENTOS, ESPERA_BLOQUEO = 5, 30 # TRAS 5 CLAVES INCORRECTAS SE BLOQUEA EL INGRESO 30 SEGUNDOS
ROLES = {"ADMIN": "Administrador", "VENDEDOR": "Vendedor"}
CLAVES_DE_EJEMPLO = {"admin123", "vendedor123"} # PUBLICADAS EN EL README: QUIEN INGRESE CON ELLAS DEBE CAMBIARLAS
# QUE PUEDE HACER CADA ROL (SE APLICA AL MENU Y TAMBIEN DENTRO DE CADA ACCION)
PERMISOS = {
    "ADMIN": {"clientes", "productos", "venta", "ventas", "reportes", "usuarios", "eliminar_cliente", "anular", "respaldo"},
    "VENDEDOR": {"clientes", "venta", "ventas"},
}

# CONSULTAS POR ENTIDAD. SIEMPRE PARAMETRIZADAS (%s): LOS DATOS VIAJAN APARTE DEL SQL, ASI NO HAY INYECCION
ENTIDADES = {
    "cliente": {
        "titulo": "Cliente", "del": "del cliente", "articulo": "al cliente", "plural": "clientes",
        "busca": """ SELECT cod_cliente, nombre, dni, telefono, sexo FROM cliente
            WHERE CAST(cod_cliente AS CHAR) = %s OR nombre LIKE %s OR dni LIKE %s ORDER BY cod_cliente """,
        "registra": "INSERT INTO cliente (nombre, dni, telefono, sexo) VALUES (%s, %s, %s, %s)",
        "actualiza": "UPDATE cliente SET nombre = %s, dni = %s, telefono = %s, sexo = %s WHERE cod_cliente = %s",
        "elimina": "DELETE FROM cliente WHERE cod_cliente = %s",
    },
    "producto": {
        "titulo": "Producto", "del": "del producto", "articulo": "el producto", "plural": "productos",
        "busca": """ SELECT cod_producto, tipo, marca, precio, cantidad FROM producto
            WHERE CAST(cod_producto AS CHAR) = %s OR tipo LIKE %s OR marca LIKE %s ORDER BY cod_producto """,
        "registra": "INSERT INTO producto (tipo, marca, precio, cantidad) VALUES (%s, %s, %s, %s)",
        "actualiza": "UPDATE producto SET tipo = %s, marca = %s, precio = %s WHERE cod_producto = %s", # EL STOCK CAMBIA SOLO CON MOVIMIENTOS
        "elimina": "DELETE FROM producto WHERE cod_producto = %s",
    },
    "usuario": {
        "titulo": "Usuario", "del": "del usuario", "articulo": "al usuario", "plural": "usuarios",
        "busca": """ SELECT cod_usuario, usuario, nombre, rol, activo FROM usuario
            WHERE CAST(cod_usuario AS CHAR) = %s OR usuario LIKE %s OR nombre LIKE %s ORDER BY cod_usuario """,
        "registra": "INSERT INTO usuario (usuario, nombre, rol, activo, clave, debe_cambiar_clave) VALUES (%s, %s, %s, %s, %s, TRUE)", # CLAVE TEMPORAL
        "actualiza": "UPDATE usuario SET usuario = %s, nombre = %s, rol = %s, activo = %s WHERE cod_usuario = %s",
        "elimina": "DELETE FROM usuario WHERE cod_usuario = %s",
    },
}
sesion = {} # USUARIO CONECTADO: cod, usuario, nombre, rol
filas = {"cliente": [], "producto": [], "usuario": [], "venta_cliente": [], "venta_producto": [], "ventas": []} # DATOS QUE MUESTRA CADA TABLA
en_edicion = {"cliente": None, "producto": None, "usuario": None} # FILA QUE SE ESTA EDITANDO (None = REGISTRO NUEVO)

# AYUDANTES GENERALES
def soles(valor):
    return f"S/ {valor:,.2f}"
def plural(cantidad, palabra, en_plural=None): # "1 venta", "3 ventas", "2 vendedores"
    return f"{cantidad} {palabra if cantidad == 1 else en_plural or palabra + 's'}"
def sin_senales(widget, cambio): # CAMBIA UN FILTRO SIN DISPARAR SU BUSQUEDA (QUIEN LLAMA BUSCA DESPUES)
    widget.blockSignals(True)
    cambio()
    widget.blockSignals(False)
def puede(permiso):
    return permiso in PERMISOS.get(sesion.get("rol"), set())
def aviso(texto, titulo=None): # NOTIFICACION FLOTANTE: AVISA SIN INTERRUMPIR
    ui.notificacion.muestra(texto, "aviso", titulo)
def informa(texto):
    ui.notificacion.muestra(texto, "exito")
def confirma(texto, titulo="Confirmar"):
    respuesta = QMessageBox.question(ventana, titulo, texto, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
    return respuesta == QMessageBox.StandardButton.Yes
def patron_like(texto): # BUSQUEDA LITERAL: % Y _ ESCRITOS POR EL USUARIO NO SON COMODINES
    return "%" + texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
def celda(texto, numero=False, etiqueta=None, orden=None): # etiqueta: "exito", "aviso", "peligro", "neutro" O "primario"
    item = interfaz.ItemTabla(str(texto))
    if numero:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if orden is None and isinstance(texto, (int, float, Decimal)):
            orden = float(texto)
    if orden is not None: # AL ORDENAR LA COLUMNA SE USA ESTE VALOR Y NO EL TEXTO
        item.setData(interfaz.ROL_ORDEN, orden)
    if etiqueta:
        item.setData(interfaz.ROL_ETIQUETA, etiqueta)
    return item
def celda_soles(valor):
    return celda(soles(valor), True, orden=float(valor))
def celda_fecha(fecha):
    return celda(f"{fecha:%d/%m/%Y}", orden=fecha.toordinal())
def etiqueta_stock(stock):
    return "peligro" if stock == 0 else "aviso" if stock <= STOCK_BAJO else None
def reconstruye_tabla(tabla, datos, celdas, codigo_elegido=None):
    # AL FILTRAR U ORDENAR, LA POSICION DE CADA REGISTRO CAMBIA: LA TABLA LO UBICA POR SU CODIGO, NO POR LA FILA
    tabla.llena(datos, celdas, codigo_elegido)
def registro_de(datos, codigo):
    return next((registro for registro in datos if registro[0] == codigo), None)
def consulta_busqueda(entidad, texto):
    texto = texto.strip()
    return bd.consulta(ENTIDADES[entidad]["busca"], (texto, patron_like(texto), patron_like(texto)))
def carpeta_descargas():
    return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation) or os.path.expanduser("~")
def pide_ruta(titulo, nombre, filtro, extension): # "GUARDAR COMO" CON NOMBRE SUGERIDO EN DESCARGAS
    ruta, _ = QFileDialog.getSaveFileName(ventana, titulo, os.path.join(carpeta_descargas(), nombre), filtro)
    if ruta and not ruta.lower().endswith(extension):
        ruta += extension
    return ruta
def ofrece_abrir(ruta, que):
    if confirma(f"{que} guardado en:\n{ruta}\n\n¿Deseas abrirlo?", f"{que} guardado"):
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))
# VALIDACIONES
def precio_numero(texto): # ACEPTA 89.90 O 89,90
    try:
        precio = Decimal(texto.strip().replace(",", "."))
    except ArithmeticError:
        return None
    return precio if precio.is_finite() and precio >= 0 else None
OBLIGATORIOS = {"cliente": ["nombre", "dni", "telefono", "sexo"], "producto": ["tipo", "marca", "precio"], "usuario": ["usuario", "nombre", "rol"]}
def esta_vacio(campo):
    return campo.currentData() is None if hasattr(campo, "currentData") else campo.text().strip() == ""
def valida(entidad, codigo_actual, campos=None):
    # DEVUELVE {CLAVE DEL CAMPO: MENSAJE} CON TODOS LOS PROBLEMAS; VACIO SI TODO ESTA BIEN
    campos = pagina(entidad).campos if campos is None else campos
    obligatorios = OBLIGATORIOS[entidad] + (["clave"] if entidad == "usuario" and not codigo_actual else [])
    errores = {clave: "Este campo es obligatorio." for clave in obligatorios if esta_vacio(campos[clave])}
    def agrega(clave, mensaje):
        errores.setdefault(clave, mensaje)
    if entidad == "cliente":
        dni, telefono = campos["dni"].text(), campos["telefono"].text()
        if dni and not (dni.isdigit() and len(dni) == 8):
            agrega("dni", "El DNI debe tener 8 dígitos.")
        elif dni:
            repetido = bd.consulta_uno("SELECT nombre FROM cliente WHERE dni = %s AND cod_cliente <> %s", (dni, codigo_actual or 0))
            if repetido:
                agrega("dni", f"Este DNI ya está registrado para {repetido[0]}.")
        if telefono and not (telefono.isdigit() and len(telefono) == 9):
            agrega("telefono", "El teléfono debe tener 9 dígitos.")
    elif entidad == "producto":
        if campos["precio"].text().strip() and precio_numero(campos["precio"].text()) is None:
            agrega("precio", "El precio debe ser un número mayor o igual a 0.")
    else:
        usuario = campos["usuario"].text().strip().lower()
        if usuario and bd.consulta_uno("SELECT 1 FROM usuario WHERE usuario = %s AND cod_usuario <> %s", (usuario, codigo_actual or 0)):
            agrega("usuario", f"El usuario «{usuario}» ya existe.")
        if campos["clave"].text() and len(campos["clave"].text()) < seguridad.LARGO_MINIMO:
            agrega("clave", f"Debe tener al menos {seguridad.LARGO_MINIMO} caracteres.")
        if codigo_actual and codigo_actual == sesion.get("cod"):
            if campos["rol"].currentData() not in (None, "ADMIN"):
                agrega("rol", "No puedes quitarte el rol de administrador.")
            if not campos["activo"].isChecked():
                agrega("activo", "No puedes desactivar tu propio usuario.")
    return errores
def limpia_errores(entidad):
    for contenedor in pagina(entidad).contenedores.values():
        contenedor.limpia_error()
def datos_formulario(entidad, campos=None): # VALORES LISTOS PARA LA BD, SIN EL CODIGO
    campos = pagina(entidad).campos if campos is None else campos
    if entidad == "cliente":
        return (campos["nombre"].text().strip(), campos["dni"].text(), campos["telefono"].text(), campos["sexo"].currentData())
    if entidad == "producto":
        return (campos["tipo"].text().strip(), campos["marca"].text().strip(), precio_numero(campos["precio"].text()), campos["stock"].value())
    return (campos["usuario"].text().strip().lower(), campos["nombre"].text().strip(), campos["rol"].currentData(), campos["activo"].isChecked())
def descripcion(entidad, datos): # TEXTO PARA LOS MENSAJES: "Juan Pérez (DNI 12345678)", "Laptop HP", "Administrador (admin)"
    if entidad == "cliente":
        return f"{datos[1]} (DNI {datos[2]})"
    if entidad == "producto":
        return f"{datos[1]} {datos[2]}"
    return f"{datos[2]} ({datos[1]})"
# NAVEGACION Y SESION
NAVEGACION = {} # nombre -> (boton del menu, pagina, funcion al abrir, permiso); SE LLENA EN conecta_eventos()
def pagina(entidad):
    return {"cliente": ui.clientes, "producto": ui.productos, "usuario": ui.usuarios}[entidad]
def entidad_de_pagina(widget):
    return {ui.clientes: "cliente", ui.productos: "producto", ui.usuarios: "usuario"}.get(widget)
def nombre_de_pagina(widget):
    return next((nombre for nombre, datos in NAVEGACION.items() if datos[1] is widget), "inicio")
def muestra_pagina(nombre):
    boton, widget, al_abrir, permiso = NAVEGACION[nombre]
    actual = ui.paginas.currentWidget()
    if permiso and not puede(permiso):
        aviso("Tu usuario no tiene permiso para esta opción.", "Sin permiso")
        NAVEGACION[nombre_de_pagina(actual)][0].setChecked(True)
        return False
    entidad = entidad_de_pagina(actual)
    if entidad and not descarta_cambios(entidad):
        NAVEGACION[nombre_de_pagina(actual)][0].setChecked(True) # EL MENU VUELVE A MARCAR LA PAGINA ACTUAL
        return False
    if entidad and widget is not actual:
        restablece_formulario(entidad) # LO NO GUARDADO SE DESCARTA AL SALIR
    boton.setChecked(True)
    ui.cambia_pagina(widget)
    if al_abrir:
        al_abrir()
    if ajustes is not None and sesion:
        ajustes.setValue(f"ultima_pagina/{sesion['usuario']}", nombre)
    return True
def autentica(usuario, clave): # DEVUELVE (DATOS DE SESION, None) O (None, MENSAJE)
    usuario = usuario.strip().lower()
    fila = bd.consulta_uno("SELECT cod_usuario, usuario, nombre, rol, activo, clave, debe_cambiar_clave FROM usuario WHERE usuario = %s", (usuario,))
    if fila is None or not seguridad.verifica_clave(clave, fila[5]):
        return None, "Usuario o contraseña incorrectos." # NO SE DICE CUAL DE LOS DOS FALLO
    if not fila[4]:
        return None, "Tu usuario está desactivado. Consulta con el administrador."
    # CONTRASEÑA TEMPORAL (LA PUSO EL ADMINISTRADOR) O LA DE EJEMPLO DEL README: SE CAMBIA ANTES DE ENTRAR
    debe_cambiar = bool(fila[6]) or clave in CLAVES_DE_EJEMPLO
    return {"cod": fila[0], "usuario": fila[1], "nombre": fila[2], "rol": fila[3], "debe_cambiar": debe_cambiar}, None
def cuenta_fallo(fallos, boton, lbl_error, mensaje): # TRAS MAX_INTENTOS FALLOS EL BOTON SE BLOQUEA ESPERA_BLOQUEO SEGUNDOS
    fallos[0] += 1
    if fallos[0] < MAX_INTENTOS:
        lbl_error.setText(mensaje)
        return
    boton.setEnabled(False)
    lbl_error.setText(f"Demasiados intentos fallidos. Espera {ESPERA_BLOQUEO} segundos.")
    def libera():
        fallos[0] = 0
        try:
            boton.setEnabled(True)
            lbl_error.setText("")
        except RuntimeError: # LA VENTANA YA SE CERRO
            pass
    QTimer.singleShot(ESPERA_BLOQUEO * 1000, libera)
def crea_dialogo_login():
    dialogo = interfaz.DialogoLogin()
    fallos = [0]
    if ajustes is not None and ajustes.value("ultimo_usuario", ""): # SE RECUERDA QUIEN INGRESO LA ULTIMA VEZ
        dialogo.txt_usuario.setText(ajustes.value("ultimo_usuario"))
        QTimer.singleShot(0, dialogo.txt_clave.setFocus)
    def ingresar():
        datos, error = autentica(dialogo.txt_usuario.text(), dialogo.txt_clave.text())
        if datos:
            sesion.clear()
            sesion.update(datos)
            if ajustes is not None:
                ajustes.setValue("ultimo_usuario", datos["usuario"])
            dialogo.accept()
            return
        dialogo.txt_clave.clear()
        dialogo.txt_clave.setFocus()
        cuenta_fallo(fallos, dialogo.btn_ingresar, dialogo.lbl_error, error)
    dialogo.btn_ingresar.clicked.connect(ingresar)
    return dialogo
def pide_login(): # True AL INGRESAR; CON CONTRASEÑA TEMPORAL O DE EJEMPLO, PRIMERO LA CAMBIA
    while crea_dialogo_login().exec() == QDialog.DialogCode.Accepted:
        if not sesion.pop("debe_cambiar", False) or crea_dialogo_clave(obligatorio=True).exec() == QDialog.DialogCode.Accepted:
            return True
        sesion.clear() # "VOLVER": DE NUEVO AL INICIO DE SESION
    return False
def iniciales(nombre):
    return "".join(palabra[0] for palabra in nombre.split()[:2]).upper()
def aplica_sesion(): # MUESTRA SOLO LO QUE EL ROL PUEDE USAR Y DEJA TODO LIMPIO
    ui.lbl_avatar.setText(iniciales(sesion["nombre"]))
    ui.lbl_sesion_nombre.setText(sesion["nombre"])
    ui.lbl_sesion_rol.setText(f"{sesion['usuario']} · {ROLES[sesion['rol']]}")
    for boton, permiso in ((ui.btn_productos, "productos"), (ui.btn_reportes, "reportes"), (ui.btn_usuarios, "usuarios"), (ui.btn_respaldo, "respaldo")):
        boton.setVisible(puede(permiso))
    ui.btn_respaldo.setToolTip(texto_ultimo_respaldo())
    ui.clientes.btn_eliminar.setVisible(puede("eliminar_cliente"))
    ui.btn_anular.setVisible(puede("anular"))
    # LAS TARJETAS DEL PANEL LLEVAN A SU DETALLE (STOCK BAJO, SOLO SI PUEDE VER PRODUCTOS)
    ui.tarjeta_hoy.hazlo_clicable(True, "Ver las ventas de hoy en el historial")
    ui.tarjeta_mes.hazlo_clicable(True, "Ver las ventas del mes en el historial")
    ui.tarjeta_clientes.hazlo_clicable(True, "Ir a Clientes")
    ui.tarjeta_stock.hazlo_clicable(puede("productos"), "Ver los productos con stock bajo")
    ui.tabla_stock_bajo.setToolTip("Haz clic en un producto para verlo" if puede("productos") else "")
    for entidad in en_edicion:
        en_edicion[entidad] = None
        estado_inicial[entidad] = None
        pagina(entidad).buscador.clear()
    sin_senales(ui.chk_stock_bajo, lambda: ui.chk_stock_bajo.setChecked(False))
    venta_actual["cliente"], venta_actual["carrito"] = None, {}
    ui.periodo_ventas.fija("Este mes")
    ui.periodo_reporte.fija("Este mes")
    sin_senales(ui.cmb_agrupar, lambda: ui.cmb_agrupar.setCurrentIndex(0))
    ultimo_reporte.clear()
    # SE ABRE LA ULTIMA PANTALLA QUE USO ESTE USUARIO, SI TODAVIA TIENE PERMISO
    ultima = ajustes.value(f"ultima_pagina/{sesion['usuario']}", "inicio") if ajustes is not None else "inicio"
    if ultima not in NAVEGACION or (NAVEGACION[ultima][3] and not puede(NAVEGACION[ultima][3])):
        ultima = "inicio"
    ui.paginas.setCurrentWidget(ui.inicio)
    muestra_pagina(ultima)
    reinicia_inactividad()
def trabajo_pendiente(): # LO QUE SE PERDERIA AL SALIR
    pendientes = [f"cambios sin guardar en {ENTIDADES[e]['plural']}" for e in en_edicion if hay_cambios(e)]
    if venta_actual["carrito"]:
        pendientes.append("una venta en curso")
    return pendientes
def puede_salir(accion):
    pendientes = trabajo_pendiente()
    return not pendientes or confirma(f"Tienes {' y '.join(pendientes)}.\n¿{accion} de todos modos?", "Hay trabajo sin guardar")
def guarda_ventana():
    if ajustes is not None and ventana is not None:
        ajustes.setValue("ventana/geometria", ventana.saveGeometry())
def cierra_sesion(preguntar=True):
    if preguntar and not puede_salir("Cerrar sesión"):
        return
    guarda_ventana()
    ui.desbloquea_pantalla()
    ventana.hide()
    sesion.clear()
    if pide_login():
        aplica_sesion()
        ventana.show()
    else:
        QApplication.quit()
class FiltroCierre(QObject): # AL CERRAR LA VENTANA: AVISA SI HAY TRABAJO SIN GUARDAR Y RECUERDA SU TAMAÑO
    def eventFilter(self, objeto, evento):
        if evento.type() == QEvent.Type.Close:
            if sesion and not puede_salir("Salir"):
                evento.ignore()
                return True
            guarda_ventana()
        return False
def crea_dialogo_clave(obligatorio=False):
    dialogo = interfaz.DialogoClave(ventana, obligatorio)
    def guardar():
        actual, nueva, repite = dialogo.txt_actual.text(), dialogo.txt_nueva.text(), dialogo.txt_repite.text()
        fila = bd.consulta_uno("SELECT clave FROM usuario WHERE cod_usuario = %s", (sesion["cod"],))
        if fila is None or (not obligatorio and not seguridad.verifica_clave(actual, fila[0])): # OBLIGATORIO: LA ACABA DE ESCRIBIR AL INGRESAR
            dialogo.lbl_error.setText("La contraseña actual no es correcta.")
        elif len(nueva) < seguridad.LARGO_MINIMO:
            dialogo.lbl_error.setText(f"La nueva contraseña debe tener al menos {seguridad.LARGO_MINIMO} caracteres.")
        elif nueva != repite:
            dialogo.lbl_error.setText("Las contraseñas nuevas no coinciden.")
        elif seguridad.verifica_clave(nueva, fila[0]):
            dialogo.lbl_error.setText("La nueva contraseña debe ser distinta de la actual.")
        elif nueva in CLAVES_DE_EJEMPLO:
            dialogo.lbl_error.setText("Esa es una contraseña de ejemplo, conocida por todos. Elige otra.")
        else:
            bd.ejecuta("UPDATE usuario SET clave = %s, debe_cambiar_clave = FALSE WHERE cod_usuario = %s", (seguridad.cifra_clave(nueva), sesion["cod"]))
            dialogo.accept()
            if ventana is not None and ventana.isVisible():
                informa("Contraseña actualizada.")
    dialogo.btn_guardar.clicked.connect(guardar)
    return dialogo
# BLOQUEO POR INACTIVIDAD: TRAS UNOS MINUTOS SIN USO SE TAPA LA PANTALLA HASTA QUE EL MISMO USUARIO ESCRIBA SU CONTRASEÑA
inactividad = None # QTimer; None SI EL BLOQUEO ESTA DESACTIVADO (bloqueo_minutos = 0)
fallos_bloqueo = [0]
class FiltroActividad(QObject): # CUALQUIER TECLA, CLIC O MOVIMIENTO DEL MOUSE REINICIA LA CUENTA
    EVENTOS = {QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress, QEvent.Type.Wheel}
    def eventFilter(self, objeto, evento):
        if evento.type() in self.EVENTOS:
            reinicia_inactividad()
        return False
def reinicia_inactividad():
    if inactividad is not None:
        inactividad.start()
def bloquea_por_inactividad():
    # NO SE BLOQUEA SIN SESION, CON LA VENTANA OCULTA (INICIO DE SESION) NI CON UN DIALOGO ABIERTO (SE ESPERA OTRA VUELTA)
    if not sesion or ventana is None or not ventana.isVisible() or ui.bloqueada() or QApplication.activeModalWidget() is not None:
        reinicia_inactividad()
        return
    bloquea()
def bloquea():
    fallos_bloqueo[0] = 0
    ui.bloqueo.btn_desbloquear.setEnabled(True)
    ui.bloquea_pantalla(sesion["nombre"], sesion["usuario"], iniciales(sesion["nombre"]))
def desbloquea():
    datos, error = autentica(sesion["usuario"], ui.bloqueo.txt_clave.text())
    if datos is not None and datos["cod"] == sesion["cod"]:
        ui.desbloquea_pantalla()
        reinicia_inactividad()
        return
    ui.bloqueo.txt_clave.clear()
    ui.bloqueo.txt_clave.setFocus()
    cuenta_fallo(fallos_bloqueo, ui.bloqueo.btn_desbloquear, ui.bloqueo.lbl_error, "La contraseña no es correcta." if error.startswith("Usuario o") else error)
def sale_del_bloqueo(): # "CERRAR SESION" DESDE LA PANTALLA DE BLOQUEO: OTRO USUARIO PUEDE INGRESAR
    if puede_salir("Cerrar sesión"):
        cierra_sesion(preguntar=False)
# RESPALDO DE LA BASE DE DATOS (SOLO ADMINISTRADOR)
def texto_ultimo_respaldo():
    ultimo = ajustes.value("respaldo/ultimo", "") if ajustes is not None else ""
    return f"Último respaldo: {ultimo}" if ultimo else "Aún no se hizo ningún respaldo"
def respalda():
    if not puede("respaldo"):
        aviso("Solo un administrador puede respaldar los datos.", "Sin permiso")
        return
    ahora = datetime.now()
    ruta = pide_ruta("Guardar respaldo", f"respaldo_{bd.config['database']}_{ahora:%Y-%m-%d_%H%M}.sql", "Respaldo SQL (*.sql)", ".sql")
    if not ruta:
        return
    try:
        filas = bd.respalda(ruta, ahora)
    except OSError as error:
        aviso(f"No se pudo guardar el respaldo: {error.strerror or error}", "Respaldo no guardado")
        return
    if ajustes is not None:
        ajustes.setValue("respaldo/ultimo", f"{ahora:%d/%m/%Y %H:%M}")
    ui.btn_respaldo.setToolTip(texto_ultimo_respaldo())
    if confirma(f"Respaldo guardado en:\n{ruta}\n\n{plural(sum(filas.values()), 'registro')} de {plural(len(filas), 'tabla')}. "
                "Guárdalo también fuera de esta PC (USB o nube).\n\n¿Deseas abrir la carpeta?", "Respaldo guardado"):
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(ruta)))
# APARIENCIA: TEMA CLARO U OSCURO Y MENU CONTRAIDO (SE RECUERDAN EN ESTA PC)
def cambia_tema():
    tema = "claro" if interfaz.tema_actual == "oscuro" else "oscuro"
    interfaz.aplica_tema(QApplication.instance(), tema)
    if ajustes is not None:
        ajustes.setValue("apariencia/tema", tema)
    muestra_detalle_venta() # SU TEXTO LLEVA COLOR
def alterna_menu():
    ui.contrae_menu(not ui.menu_contraido)
    if ajustes is not None:
        ajustes.setValue("apariencia/menu_contraido", ui.menu_contraido)
# PANEL DE INICIO
def tendencia(actual, anterior, comparado, sin_ventas): # (TEXTO, SENTIDO): LA FLECHA Y EL SIGNO DICEN SI SUBIO, NO SOLO EL COLOR
    if actual == anterior:
        return f"= igual que {comparado}", None
    if anterior == 0:
        return f"▲ {sin_ventas}", "sube"
    cambio = (actual - anterior) / anterior * 100
    if abs(cambio) < 0.5:
        return f"= igual que {comparado}", None
    return (f"▲ +{cambio:.0f}% vs {comparado}", "sube") if cambio > 0 else (f"▼ −{abs(cambio):.0f}% vs {comparado}", "baja")
def ventas_por_dia(inicio, fin): # {fecha: (total, cantidad)} DE LAS VENTAS REGISTRADAS
    return {fila[0]: (fila[1], fila[2]) for fila in bd.consulta(""" SELECT fecha, SUM(total), COUNT(*) FROM venta
        WHERE estado = 'REGISTRADA' AND fecha BETWEEN %s AND %s GROUP BY fecha """, (inicio, fin))}
def barras_por_dia(inicio, fin, ventas): # LOS DIAS SIN VENTAS TAMBIEN APARECEN (EN CERO) PARA NO ENGAÑAR AL OJO
    dias = (fin - inicio).days + 1
    barras = []
    for numero in range(dias):
        dia = inicio + timedelta(days=numero)
        total, cantidad = ventas.get(dia, (0, 0))
        etiqueta = f"{DIAS[dia.weekday()][:3]} {dia.day}" if dias <= 7 else f"{dia:%d/%m}"
        barras.append((etiqueta, total, f"{DIAS[dia.weekday()].capitalize()} {dia:%d/%m/%Y}\n{soles(total)} · {plural(cantidad, 'venta')}"))
    return barras
def barras_por_mes(inicio, fin, ventas): # PERIODOS LARGOS: UNA BARRA POR MES
    meses = {}
    for dia, (total, cantidad) in ventas.items():
        acumulado = meses.get((dia.year, dia.month), (0, 0))
        meses[(dia.year, dia.month)] = (acumulado[0] + total, acumulado[1] + cantidad)
    barras, anio, mes = [], inicio.year, inicio.month
    while (anio, mes) <= (fin.year, fin.month):
        total, cantidad = meses.get((anio, mes), (0, 0))
        barras.append((f"{MESES[mes - 1][:3]} {anio % 100:02d}", total, f"{MESES[mes - 1]} {anio}\n{soles(total)} · {plural(cantidad, 'venta')}"))
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return barras
def abre_inicio():
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    inicio_mes, fin_mes = date(hoy.year, hoy.month, 1), date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
    inicio_anterior = (inicio_mes - timedelta(days=1)).replace(day=1) # EL MES ANTERIOR, HASTA EL MISMO DIA (O SU ULTIMO DIA)
    fin_anterior = inicio_anterior.replace(day=min(hoy.day, calendar.monthrange(inicio_anterior.year, inicio_anterior.month)[1]))
    ui.lbl_saludo.setText(f"Hola, {sesion.get('nombre', '')}")
    ui.lbl_fecha_hoy.setText(f"{DIAS[hoy.weekday()].capitalize()} {hoy.day} de {MESES[hoy.month - 1].lower()} de {hoy.year}")
    resumen = """ SELECT COUNT(*), COALESCE(SUM(total), 0) FROM venta WHERE estado = 'REGISTRADA' AND fecha BETWEEN %s AND %s """
    cantidad, total = bd.consulta_uno(resumen, (hoy, hoy))
    total_ayer = bd.consulta_uno(resumen, (ayer, ayer))[1]
    ui.tarjeta_hoy.valor.setText(soles(total))
    ui.tarjeta_hoy.detalle.setText(plural(cantidad, "venta"))
    ui.tarjeta_hoy.muestra_tendencia(*tendencia(total, total_ayer, "ayer", "ayer no hubo ventas"), f"Ayer ({ayer:%d/%m}) se vendió {soles(total_ayer)}")
    cantidad, total = bd.consulta_uno(resumen, (inicio_mes, fin_mes))
    hasta_hoy = bd.consulta_uno(resumen, (inicio_mes, hoy))[1]
    total_anterior = bd.consulta_uno(resumen, (inicio_anterior, fin_anterior))[1]
    mes_anterior = MESES[inicio_anterior.month - 1].lower()
    ui.tarjeta_mes.valor.setText(soles(total))
    ui.tarjeta_mes.detalle.setText(plural(cantidad, "venta"))
    ui.tarjeta_mes.muestra_tendencia(*tendencia(hasta_hoy, total_anterior, f"{mes_anterior[:3]}.", f"sin ventas en {mes_anterior[:3]}."),
                                     f"Del 1 al {fin_anterior.day} de {mes_anterior} se vendió {soles(total_anterior)}")
    ui.tarjeta_clientes.valor.setText(str(bd.consulta_uno("SELECT COUNT(*) FROM cliente")[0]))
    ui.tarjeta_clientes.detalle.setText("registrados")
    stock_bajo = bd.consulta("SELECT cod_producto, CONCAT(tipo, ' ', marca), cantidad FROM producto WHERE cantidad <= %s ORDER BY cantidad, tipo", (STOCK_BAJO,))
    ui.tarjeta_stock.valor.setText(str(len(stock_bajo)))
    ui.tarjeta_stock.detalle.setText("con 5 unidades o menos" if stock_bajo else "Todo el stock está en orden")
    reconstruye_tabla(ui.tabla_stock_bajo, stock_bajo,
                      lambda datos: [celda(datos[1]), celda("Agotado" if datos[2] == 0 else datos[2], True, etiqueta_stock(datos[2]))])
    mas_vendidos = bd.consulta(""" SELECT p.cod_producto, CONCAT(p.tipo, ' ', p.marca), SUM(d.cantidad), SUM(d.cantidad * d.precio_unitario)
        FROM det_venta d
        INNER JOIN venta v ON v.num_venta = d.num_venta
        INNER JOIN producto p ON p.cod_producto = d.cod_producto
        WHERE v.estado = 'REGISTRADA' AND v.fecha BETWEEN %s AND %s
        GROUP BY p.cod_producto, p.tipo, p.marca
        ORDER BY 3 DESC, 4 DESC LIMIT 5 """, (inicio_mes, fin_mes))
    maximo = max((fila[2] for fila in mas_vendidos), default=1)
    ui.lista_mas_vendidos.muestra([(codigo, nombre, f"{unidades} unid. · {soles(importe)}", float(unidades / maximo))
                                   for codigo, nombre, unidades, importe in mas_vendidos], puede("productos"))
    muestra_grafico_inicio()
def muestra_grafico_inicio(): # VENTAS DE LOS ULTIMOS 7 O 30 DIAS
    dias = 7 if ui.btn_7_dias.isChecked() else 30
    fin = date.today()
    inicio = fin - timedelta(days=dias - 1)
    ventas = ventas_por_dia(inicio, fin)
    ui.grafico_inicio.muestra(barras_por_dia(inicio, fin, ventas))
    total = sum((total for total, _ in ventas.values()), Decimal("0"))
    ui.lbl_resumen_grafico.setText(f"Últimos {dias} días  ·  {soles(total)} en {plural(sum(c for _, c in ventas.values()), 'venta')}")
def abre_historial(periodo, texto="", desde=None, hasta=None): # LLEGA AL HISTORIAL CON LOS FILTROS LISTOS
    ui.periodo_ventas.fija(periodo, desde, hasta)
    sin_senales(ui.cmb_estado_venta, lambda: ui.cmb_estado_venta.setCurrentIndex(0))
    sin_senales(ui.buscador_ventas, lambda: ui.buscador_ventas.setText(texto))
    muestra_pagina("ventas")
def abre_producto(codigo=None, solo_stock_bajo=False): # LA LISTA DE PRODUCTOS SIN BUSQUEDA (O SOLO STOCK BAJO) Y EL PRODUCTO ELEGIDO
    if not puede("productos"):
        return
    sin_senales(ui.productos.buscador, ui.productos.buscador.clear)
    sin_senales(ui.chk_stock_bajo, lambda: ui.chk_stock_bajo.setChecked(solo_stock_bajo))
    if muestra_pagina("productos") and codigo is not None:
        selecciona_codigo("producto", codigo)
# CLIENTES, PRODUCTOS Y USUARIOS (MISMA PANTALLA: TABLA + FORMULARIO)
def abre_entidad(entidad):
    busca(entidad)
    if en_edicion[entidad] is None:
        nuevo(entidad)
    else:
        selecciona_codigo(entidad, en_edicion[entidad][0])
def busca(entidad):
    p = pagina(entidad)
    texto = p.buscador.text().strip()
    filas[entidad] = consulta_busqueda(entidad, texto)
    solo_stock_bajo = entidad == "producto" and ui.chk_stock_bajo.isChecked()
    if solo_stock_bajo:
        filas[entidad] = [fila for fila in filas[entidad] if fila[4] <= STOCK_BAJO]
    def celdas(datos):
        if entidad == "cliente":
            return [celda(datos[0], True), celda(datos[1]), celda(datos[2]), celda(datos[3]), celda(datos[4].capitalize())]
        if entidad == "producto":
            return [celda(datos[0], True), celda(datos[1]), celda(datos[2]), celda_soles(datos[3]),
                    celda(datos[4], True, etiqueta_stock(datos[4]))] # AGOTADO EN ROJO, STOCK BAJO EN AMBAR
        return [celda(datos[0], True), celda(datos[1]), celda(datos[2]),
                celda(ROLES[datos[3]], etiqueta="primario" if datos[3] == "ADMIN" else "neutro"),
                celda("Sí" if datos[4] else "No", etiqueta="exito" if datos[4] else "peligro")]
    nombre_plural = ENTIDADES[entidad]["plural"]
    if solo_stock_bajo:
        p.tabla.mostrar_vacio("No hay productos con stock bajo" + (f" que coincidan con «{texto}»." if texto else ". ¡Todo en orden!"))
    else:
        p.tabla.mostrar_vacio(f"No hay {nombre_plural} que coincidan con «{texto}»." if texto
                              else f"Aún no hay {nombre_plural}. Pulsa «Nuevo» para registrar el primero.")
    reconstruye_tabla(p.tabla, filas[entidad], celdas, en_edicion[entidad][0] if en_edicion[entidad] else None)
    total = len(filas[entidad])
    p.lbl_conteo.setText(f"{total} {nombre_plural if total != 1 else entidad}" + (" con stock bajo" if solo_stock_bajo else ""))
# CAMBIOS SIN GUARDAR: SE COMPARA EL FORMULARIO CON COMO ESTABA AL ABRIRLO
estado_inicial = {"cliente": None, "producto": None, "usuario": None}
def valores_formulario(entidad):
    valores = []
    for clave, campo in pagina(entidad).campos.items():
        if clave == "codigo":
            continue
        if hasattr(campo, "currentData"):
            valores.append(campo.currentData())
        elif hasattr(campo, "value"):
            valores.append(campo.value())
        elif isinstance(campo, QCheckBox):
            valores.append(campo.isChecked())
        else:
            valores.append(campo.text())
    return tuple(valores)
def marca_guardado(entidad):
    estado_inicial[entidad] = valores_formulario(entidad)
def hay_cambios(entidad):
    return estado_inicial[entidad] is not None and valores_formulario(entidad) != estado_inicial[entidad]
def descarta_cambios(entidad): # True SI NO HAY CAMBIOS O EL USUARIO ACEPTA PERDERLOS
    if not hay_cambios(entidad):
        return True
    return confirma(f"Tienes cambios sin guardar en el formulario {ENTIDADES[entidad]['del']}.\n¿Quieres descartarlos?", "Cambios sin guardar")
def restablece_formulario(entidad): # VUELVE A LOS DATOS GUARDADOS
    if en_edicion[entidad] is None:
        nuevo(entidad)
    else:
        carga_formulario(entidad, en_edicion[entidad])
def nuevo(entidad, preguntar=False):
    if preguntar and not descarta_cambios(entidad):
        return
    p = pagina(entidad)
    en_edicion[entidad] = None
    p.tabla.clearSelection()
    limpia_errores(entidad)
    for campo in p.campos.values():
        if hasattr(campo, "setCurrentIndex"):
            campo.setCurrentIndex(0)
        elif hasattr(campo, "setValue"):
            campo.setValue(0)
        elif isinstance(campo, QCheckBox):
            campo.setChecked(True)
        else:
            campo.clear()
    p.campos["codigo"].setText(bd.siguiente_codigo(entidad))
    if entidad == "usuario":
        p.campos["clave"].setPlaceholderText(f"Mínimo {seguridad.LARGO_MINIMO} caracteres")
        p.contenedores["clave"].cambia_ayuda("Es temporal: la cambiará al ingresar por primera vez.")
    if entidad == "producto":
        modo_stock(True)
    p.grupo.setTitle(f"Nuevo {entidad}")
    p.btn_guardar.setText(f"Registrar {entidad}")
    p.btn_eliminar.setEnabled(False)
    if entidad == "cliente":
        muestra_compras_cliente()
    marca_guardado(entidad)
def carga_formulario(entidad, datos): # LOS DATOS DEL REGISTRO PASAN AL FORMULARIO PARA EDITARLOS
    p = pagina(entidad)
    en_edicion[entidad] = datos
    limpia_errores(entidad)
    campos = p.campos
    campos["codigo"].setText(str(datos[0]))
    if entidad == "cliente":
        campos["nombre"].setText(datos[1])
        campos["dni"].setText(datos[2])
        campos["telefono"].setText(datos[3])
        campos["sexo"].setCurrentIndex(max(campos["sexo"].findData(datos[4].upper()), 0))
    elif entidad == "producto":
        campos["tipo"].setText(datos[1])
        campos["marca"].setText(datos[2])
        campos["precio"].setText(f"{datos[3]:.2f}")
        campos["stock"].setValue(datos[4])
        modo_stock(False)
    else:
        campos["usuario"].setText(datos[1])
        campos["nombre"].setText(datos[2])
        campos["rol"].setCurrentIndex(max(campos["rol"].findData(datos[3]), 0))
        campos["activo"].setChecked(bool(datos[4]))
        campos["clave"].clear()
        campos["clave"].setPlaceholderText("Déjala vacía para no cambiarla")
        p.contenedores["clave"].cambia_ayuda("" if datos[0] == sesion.get("cod") else "Si escribes una, será temporal y la cambiará al ingresar.")
    p.grupo.setTitle(f"Editar {entidad} N° {datos[0]}")
    p.btn_guardar.setText("Guardar cambios")
    p.btn_eliminar.setEnabled(True)
    if entidad == "cliente":
        muestra_compras_cliente()
    marca_guardado(entidad)
def muestra_compras_cliente(): # TOTAL GASTADO, N° DE COMPRAS Y ULTIMA COMPRA DEL CLIENTE ELEGIDO (LAS ANULADAS NO CUENTAN)
    datos = en_edicion["cliente"]
    ui.grupo_compras.setVisible(datos is not None)
    if datos is None:
        return
    todas, compras, gastado, ultima = bd.consulta_uno(""" SELECT COUNT(*), COALESCE(SUM(estado = 'REGISTRADA'), 0),
            COALESCE(SUM(CASE WHEN estado = 'REGISTRADA' THEN total END), 0), MAX(CASE WHEN estado = 'REGISTRADA' THEN fecha END)
        FROM venta WHERE cod_cliente = %s """, (datos[0],))
    ui.caja_cifras.setVisible(compras > 0)
    ui.lbl_sin_compras.setVisible(compras == 0)
    ui.lbl_sin_compras.setText("Sus ventas fueron anuladas." if todas else "Aún no tiene compras registradas.")
    ui.btn_ver_compras.setVisible(todas > 0)
    ui.lbl_total_gastado.setText(soles(gastado))
    ui.lbl_num_compras.setText(str(int(compras)))
    ui.lbl_ultima_compra.setText(f"{ultima:%d/%m/%Y}" if ultima else "-")
def ver_compras_cliente(): # EL HISTORIAL FILTRADO POR SU DNI, DESDE SU PRIMERA COMPRA
    datos = en_edicion["cliente"]
    primera = bd.consulta_uno("SELECT MIN(fecha) FROM venta WHERE cod_cliente = %s", (datos[0],))[0] if datos else None
    if primera is not None:
        abre_historial("Personalizado", datos[2], QDate(primera.year, primera.month, primera.day), QDate.currentDate())
def selecciona(entidad): # AL ELEGIR UNA FILA: SI HAY CAMBIOS SIN GUARDAR SE PREGUNTA ANTES DE REEMPLAZARLOS
    p = pagina(entidad)
    codigo = p.tabla.codigo_seleccionado()
    datos = registro_de(filas[entidad], codigo)
    if datos is None:
        return
    anterior = en_edicion[entidad][0] if en_edicion[entidad] else None
    if codigo == anterior:
        return
    if not descarta_cambios(entidad): # SE QUEDA EN EL REGISTRO QUE SE ESTABA EDITANDO
        p.tabla.blockSignals(True)
        p.tabla.clearSelection()
        fila = p.tabla.fila_de_codigo(anterior)
        if fila is not None:
            p.tabla.selectRow(fila)
        p.tabla.blockSignals(False)
        return
    carga_formulario(entidad, datos)
def selecciona_codigo(entidad, codigo): # MARCA EL REGISTRO Y CARGA EN EL FORMULARIO SUS DATOS ACTUALES
    p = pagina(entidad)
    fila, datos = p.tabla.fila_de_codigo(codigo), registro_de(filas[entidad], codigo)
    if fila is None or datos is None:
        nuevo(entidad) # YA NO APARECE CON EL FILTRO ACTUAL
        return
    p.tabla.blockSignals(True)
    p.tabla.selectRow(fila)
    p.tabla.blockSignals(False)
    carga_formulario(entidad, datos)
def guardar(entidad):
    datos_actuales = en_edicion[entidad]
    codigo = datos_actuales[0] if datos_actuales else None
    errores = valida(entidad, codigo)
    p = pagina(entidad)
    limpia_errores(entidad) # SE RECALCULAN TODOS: NO QUEDAN ERRORES VIEJOS DE CAMPOS YA CORREGIDOS
    if errores: # CADA ERROR SE MUESTRA DEBAJO DE SU CAMPO Y EL CURSOR VA AL PRIMERO
        for clave, mensaje in errores.items():
            p.contenedores[clave].muestra_error(mensaje)
        primero = next(clave for clave in p.campos if clave in errores)
        p.campos[primero].setFocus()
        aviso("Revisa los campos marcados en rojo.")
        return
    titulo = ENTIDADES[entidad]["titulo"]
    datos = datos_formulario(entidad)
    clave = pagina(entidad).campos["clave"].text() if entidad == "usuario" else ""
    if codigo is None:
        if entidad == "usuario":
            datos += (seguridad.cifra_clave(clave),)
        nuevo_codigo = bd.ejecuta(ENTIDADES[entidad]["registra"], datos) # EL CODIGO LO ASIGNA LA BD
        busca(entidad)
        nuevo(entidad) # LISTO PARA REGISTRAR EL SIGUIENTE
        informa(f"{titulo} registrado con código {nuevo_codigo}.")
        list(pagina(entidad).campos.values())[1].setFocus()
    else:
        with bd.cursor_bd() as cursor:
            valores = datos[:3] if entidad == "producto" else datos # SIN EL STOCK
            cursor.execute(ENTIDADES[entidad]["actualiza"], valores + (codigo,))
            if clave: # SOLO SI SE ESCRIBIO UNA NUEVA; SI ES DE OTRO USUARIO, ES TEMPORAL Y LA CAMBIARA AL INGRESAR
                cursor.execute("UPDATE usuario SET clave = %s, debe_cambiar_clave = %s WHERE cod_usuario = %s",
                               (seguridad.cifra_clave(clave), codigo != sesion.get("cod"), codigo))
        busca(entidad)
        selecciona_codigo(entidad, codigo)
        informa(f"Cambios guardados en {entidad} N° {codigo}.")
def eliminar(entidad):
    datos = en_edicion[entidad]
    if datos is None:
        return
    if entidad == "cliente" and not puede("eliminar_cliente"):
        aviso("Tu usuario no tiene permiso para eliminar clientes.", "Sin permiso")
        return
    if entidad == "usuario" and datos[0] == sesion.get("cod"):
        aviso("No puedes eliminar tu propio usuario.")
        return
    texto = f"{ENTIDADES[entidad]['articulo']} {descripcion(entidad, datos)}" # "al cliente Juan Pérez (DNI ...)" / "el producto Laptop HP"
    if not confirma(f"¿Eliminar {texto}?\nEsta acción no se puede deshacer."):
        return
    try:
        bd.ejecuta(ENTIDADES[entidad]["elimina"], (datos[0],))
    except pymysql.err.IntegrityError:
        sugerencia = " Puedes desactivarlo para que ya no ingrese." if entidad == "usuario" else ""
        aviso(f"No se puede eliminar {texto} porque tiene ventas registradas.{sugerencia}", "No se puede eliminar")
        return
    busca(entidad)
    nuevo(entidad)
    informa(f"{ENTIDADES[entidad]['titulo']} eliminado.")
# MOVIMIENTO DE STOCK: SUMA O RESTA SOBRE EL VALOR REAL DE LA BD, NUNCA LO REEMPLAZA (ASI NO SE PISA UNA VENTA SIMULTANEA)
def modo_stock(editable): # SOLO SE ESCRIBE AL CREAR EL PRODUCTO; LUEGO SE USA "INGRESAR O RETIRAR STOCK"
    campo = ui.productos.campos["stock"]
    campo.setReadOnly(not editable)
    campo.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows if editable else QAbstractSpinBox.ButtonSymbols.NoButtons)
    interfaz.repule(campo)
    ui.productos.contenedores["stock"].cambia_ayuda("Stock inicial del producto" if editable else "Para cambiarlo usa «Ingresar o retirar stock».")
    ui.btn_stock.setVisible(not editable)
def crea_dialogo_stock():
    datos = en_edicion["producto"]
    if datos is None:
        return None
    stock = bd.consulta_uno("SELECT cantidad FROM producto WHERE cod_producto = %s", (datos[0],))[0]
    nombre = descripcion("producto", datos)
    dialogo = interfaz.DialogoStock(ventana, nombre, stock)
    def cambio():
        return dialogo.cmb_tipo.currentData() * dialogo.spn_cantidad.value()
    def actualiza():
        resultado = stock + cambio()
        dialogo.lbl_resultado.setText(f"Stock después del movimiento: {resultado} unid.")
        dialogo.lbl_error.setText("" if resultado >= 0 else f"No puedes retirar más de {stock} unidades.")
        dialogo.btn_guardar.setEnabled(resultado >= 0)
    def aplicar():
        try:
            with bd.cursor_bd() as cursor:
                cursor.execute("UPDATE producto SET cantidad = cantidad + %s WHERE cod_producto = %s AND cantidad + %s >= 0",
                               (cambio(), datos[0], cambio()))
                if cursor.rowcount == 0:
                    raise ValueError
        except ValueError:
            dialogo.lbl_error.setText("El stock cambió mientras tanto (quizá por una venta) y no alcanza para esta salida.")
            return
        nuevo_stock = bd.consulta_uno("SELECT cantidad FROM producto WHERE cod_producto = %s", (datos[0],))[0]
        dialogo.accept()
        busca("producto")
        selecciona_codigo("producto", datos[0])
        informa(f"Stock de {nombre}: {stock} → {nuevo_stock} unid.")
    dialogo.cmb_tipo.currentIndexChanged.connect(actualiza)
    dialogo.spn_cantidad.valueChanged.connect(actualiza)
    dialogo.btn_guardar.clicked.connect(aplicar)
    actualiza()
    return dialogo
def abre_dialogo_stock():
    dialogo = crea_dialogo_stock()
    if dialogo is not None:
        dialogo.exec()
# VENTA
CLIENTE_VARIOS = (None, "Cliente varios", None) # VENTA RAPIDA SIN CLIENTE REGISTRADO (cod_cliente = NULL)
venta_actual = {"cliente": None, "carrito": {}} # carrito: cod_producto -> {producto, precio, cantidad, stock}
def abre_venta():
    busca_clientes_venta()
    busca_productos_venta()
    ui.lbl_num_venta.setText(f"Venta N° {bd.siguiente_codigo('venta')}  ·  {date.today():%d/%m/%Y}")
    muestra_cliente_venta()
    muestra_carrito()
def busca_clientes_venta():
    texto = ui.buscador_cliente_venta.text().strip()
    filas["venta_cliente"] = consulta_busqueda("cliente", texto)
    cliente = venta_actual["cliente"]
    ui.tabla_clientes_venta.mostrar_vacio(f"No hay clientes que coincidan con «{texto}»." if texto else "Aún no hay clientes registrados.")
    reconstruye_tabla(ui.tabla_clientes_venta, filas["venta_cliente"],
                      lambda datos: [celda(datos[0], True), celda(datos[1]), celda(datos[2])], cliente[0] if cliente else None)
def busca_productos_venta():
    elegido = ui.tabla_productos_venta.codigo_seleccionado()
    texto = ui.buscador_producto_venta.text().strip()
    filas["venta_producto"] = consulta_busqueda("producto", texto)
    ui.tabla_productos_venta.mostrar_vacio(f"No hay productos que coincidan con «{texto}»." if texto else "Aún no hay productos registrados.")
    reconstruye_tabla(ui.tabla_productos_venta, filas["venta_producto"],
                      lambda datos: [celda(datos[0], True), celda(datos[1]), celda(datos[2]), celda_soles(datos[3]),
                                     celda(datos[4], True, etiqueta_stock(datos[4]))], elegido)
    actualiza_disponible()
def selecciona_cliente_venta():
    registro = registro_de(filas["venta_cliente"], ui.tabla_clientes_venta.codigo_seleccionado())
    if registro is not None:
        codigo, nombre, dni, _, _ = registro
        venta_actual["cliente"] = (codigo, nombre, dni)
    muestra_cliente_venta()
def es_cliente_varios():
    return venta_actual["cliente"] is not None and venta_actual["cliente"][0] is None
def elige_cliente_varios():
    venta_actual["cliente"] = CLIENTE_VARIOS
    ui.tabla_clientes_venta.clearSelection()
    if forma_pago() == "Crédito": # A CREDITO SE NECESITA SABER QUIEN DEBE
        ui.btn_contado.setChecked(True)
        aviso("Las ventas a «Cliente varios» son solo al contado.", "Forma de pago")
    muestra_cliente_venta()
def muestra_cliente_venta(): # EL CLIENTE ELEGIDO SE VE COMO UNA FICHA EN EL TICKET
    cliente = venta_actual["cliente"]
    if cliente is None:
        texto, iniciales = "<b>Ningún cliente elegido</b><br>Elige uno de la lista o usa «Cliente varios».", "?"
    elif es_cliente_varios():
        texto, iniciales = "<b>Cliente varios</b><br>Venta sin cliente registrado", "CV"
    else:
        texto = f"<b>{escape(cliente[1])}</b><br>DNI {cliente[2]}"
        iniciales = "".join(palabra[0] for palabra in cliente[1].split()[:2]).upper()
    ui.lbl_cliente_venta.setText(texto)
    ui.lbl_iniciales_cliente.setText(iniciales)
    for widget in (ui.chip_cliente, ui.lbl_iniciales_cliente):
        widget.setProperty("vacio", cliente is None)
        interfaz.repule(widget)
    ui.btn_credito.setEnabled(not es_cliente_varios())
    ui.btn_credito.setToolTip("Las ventas a «Cliente varios» son solo al contado." if es_cliente_varios() else "")
    actualiza_botones_venta()
def crea_dialogo_cliente(): # "NUEVO CLIENTE" SIN SALIR DE LA VENTA; QUEDA ELEGIDO AL REGISTRARLO
    dialogo = interfaz.DialogoCliente(ventana)
    def registrar():
        for contenedor in dialogo.contenedores.values():
            contenedor.limpia_error()
        errores = valida("cliente", None, dialogo.campos)
        if errores:
            for clave, mensaje in errores.items():
                dialogo.contenedores[clave].muestra_error(mensaje)
            dialogo.campos[next(clave for clave in dialogo.campos if clave in errores)].setFocus()
            return
        datos = datos_formulario("cliente", dialogo.campos)
        codigo = bd.ejecuta(ENTIDADES["cliente"]["registra"], datos)
        venta_actual["cliente"] = (codigo, datos[0], datos[1])
        dialogo.accept()
        ui.buscador_cliente_venta.blockSignals(True)
        ui.buscador_cliente_venta.clear()
        ui.buscador_cliente_venta.blockSignals(False)
        busca_clientes_venta()
        muestra_cliente_venta()
        informa(f"Cliente registrado con código {codigo} y elegido para esta venta.")
    dialogo.btn_guardar.clicked.connect(registrar)
    for campo in dialogo.campos.values():
        if hasattr(campo, "returnPressed"):
            campo.returnPressed.connect(registrar)
    return dialogo
def producto_venta_seleccionado():
    return registro_de(filas["venta_producto"], ui.tabla_productos_venta.codigo_seleccionado())
def actualiza_disponible(): # LA CANTIDAD NO PUEDE SUPERAR EL STOCK MENOS LO QUE YA ESTA EN LA VENTA
    producto = producto_venta_seleccionado()
    if producto is None:
        disponible = 0
        ui.lbl_disponible.setText("Selecciona un producto")
    else:
        en_carrito = venta_actual["carrito"].get(producto[0], {}).get("cantidad", 0)
        disponible = producto[4] - en_carrito
        ui.lbl_disponible.setText(f"Disponibles: {disponible}" if disponible > 0 else "Sin stock disponible")
    ui.spn_cantidad.setMaximum(max(disponible, 1))
    ui.spn_cantidad.setEnabled(disponible > 0)
    ui.btn_agregar.setEnabled(disponible > 0)
def agrega_producto():
    producto = producto_venta_seleccionado()
    if producto is None:
        aviso("Selecciona un producto de la lista.")
        return False
    codigo = producto[0]
    actual = bd.consulta_uno("SELECT tipo, marca, precio, cantidad FROM producto WHERE cod_producto = %s", (codigo,))
    if actual is None:
        aviso("El producto ya no existe.")
        busca_productos_venta()
        return False
    tipo, marca, precio, stock = actual
    en_carrito = venta_actual["carrito"].get(codigo, {}).get("cantidad", 0)
    cantidad = en_carrito + ui.spn_cantidad.value()
    if cantidad > stock:
        aviso(f"Solo quedan {stock} unidades de {tipo} {marca}." + (f" Ya tienes {en_carrito} en esta venta." if en_carrito else ""), "Stock insuficiente")
        return False
    venta_actual["carrito"][codigo] = {"producto": f"{tipo} {marca}", "precio": precio, "cantidad": cantidad, "stock": stock}
    ui.spn_cantidad.setValue(1)
    muestra_carrito()
    return True
def agrega_por_codigo(): # ENTER EN EL BUSCADOR (O LECTOR DE CODIGO DE BARRAS): AGREGA SI HAY UN SOLO PRODUCTO POSIBLE
    texto = ui.buscador_producto_venta.text().strip()
    busca_productos_venta()
    if not texto:
        return
    exacto = [fila for fila in filas["venta_producto"] if str(fila[0]) == texto]
    candidatos = exacto or filas["venta_producto"]
    if len(candidatos) != 1:
        aviso(f"No hay productos que coincidan con «{texto}»." if not candidatos
              else f"Hay {len(candidatos)} productos que coinciden con «{texto}». Elige uno de la lista.")
        return
    ui.tabla_productos_venta.selectRow(ui.tabla_productos_venta.fila_de_codigo(candidatos[0][0]))
    if agrega_producto(): # LISTO PARA EL SIGUIENTE CODIGO
        ui.buscador_producto_venta.clear()
        ui.buscador_producto_venta.setFocus()
def quita_producto(codigo):
    venta_actual["carrito"].pop(codigo, None)
    muestra_carrito()
def cambia_cantidad(codigo, cantidad): # LA CANTIDAD SE EDITA DIRECTO EN EL TICKET
    linea = venta_actual["carrito"].get(codigo)
    if linea is None:
        return
    linea["cantidad"] = cantidad
    for fila in ui.detalle_venta.lineas:
        if fila.codigo == codigo:
            fila.lbl_subtotal.setText(soles(linea["precio"] * cantidad))
    actualiza_totales()
    actualiza_disponible()
def total_carrito():
    return sum((linea["precio"] * linea["cantidad"] for linea in venta_actual["carrito"].values()), Decimal("0"))
def muestra_carrito():
    ui.detalle_venta.limpia()
    for codigo, linea in venta_actual["carrito"].items():
        fila = interfaz.LineaVenta(codigo, linea["producto"], soles(linea["precio"]), linea["cantidad"], linea["stock"])
        fila.lbl_subtotal.setText(soles(linea["precio"] * linea["cantidad"]))
        fila.spn_cantidad.valueChanged.connect(lambda valor, c=codigo: cambia_cantidad(c, valor))
        fila.btn_quitar.clicked.connect(lambda _marcado=False, c=codigo: quita_producto(c))
        ui.detalle_venta.agrega(fila)
    actualiza_totales()
    actualiza_disponible()
def forma_pago():
    return "Contado" if ui.btn_contado.isChecked() else "Crédito"
def monto_recibido(): # None SI NO SE ESCRIBIO (NO ES OBLIGATORIO)
    return precio_numero(ui.txt_recibido.text()) if ui.txt_recibido.text().strip() else None
def actualiza_totales(): # TOTAL, VUELTO Y BOTONES
    total = total_carrito()
    ui.lbl_total.setText(soles(total))
    contado = forma_pago() == "Contado"
    ui.caja_recibido.setVisible(contado)
    recibido = monto_recibido() if contado else None
    falta = recibido is not None and recibido < total
    if recibido is None:
        ui.lbl_vuelto.setText("")
    elif falta:
        ui.lbl_vuelto.setText(f"Falta {soles(total - recibido)}")
    else:
        ui.lbl_vuelto.setText(f"Vuelto: {soles(recibido - total)}")
    ui.lbl_vuelto.setProperty("falta", falta)
    interfaz.repule(ui.lbl_vuelto)
    actualiza_botones_venta()
def actualiza_botones_venta():
    hay_productos, hay_cliente = bool(venta_actual["carrito"]), venta_actual["cliente"] is not None
    ui.btn_registrar_venta.setEnabled(hay_productos and hay_cliente)
    ui.btn_registrar_venta.setToolTip("" if hay_cliente else "Primero elige el cliente")
    ui.btn_cancelar_venta.setEnabled(hay_productos or hay_cliente)
def reinicia_venta():
    venta_actual["cliente"] = None
    venta_actual["carrito"] = {}
    for campo in (ui.buscador_cliente_venta, ui.buscador_producto_venta, ui.txt_recibido):
        campo.blockSignals(True)
        campo.clear()
        campo.blockSignals(False)
    ui.btn_contado.setChecked(True)
    ui.spn_cantidad.setValue(1)
    abre_venta()
def cancela_venta():
    if venta_actual["carrito"] and not confirma("¿Descartar los productos de la venta en curso?"):
        return
    reinicia_venta()
def registra_venta():
    cliente, carrito = venta_actual["cliente"], venta_actual["carrito"]
    if not carrito:
        aviso("Agrega al menos un producto a la venta.")
        return
    if cliente is None:
        aviso("Selecciona el cliente de la venta.")
        return
    pago = forma_pago()
    if pago == "Crédito" and es_cliente_varios():
        aviso("Las ventas a crédito necesitan un cliente registrado.", "Forma de pago")
        return
    recibido = monto_recibido() if pago == "Contado" else None
    if recibido is not None and recibido < total_carrito():
        aviso(f"El monto recibido no alcanza: faltan {soles(total_carrito() - recibido)}.", "Pago incompleto")
        ui.txt_recibido.setFocus()
        return
    if not confirma(f"¿Registrar la venta de {soles(total_carrito())} a {cliente[1]} ({pago.lower()})?", "Registrar venta"):
        return
    try:
        with bd.cursor_bd() as cursor: # TODO O NADA: CABECERA, DETALLE Y STOCK
            total = Decimal("0")
            precios = {}
            for cod_producto, linea in carrito.items():
                # FOR UPDATE BLOQUEA EL PRODUCTO HASTA TERMINAR, ASI DOS VENTAS NO VENDEN EL MISMO STOCK
                cursor.execute("SELECT tipo, marca, precio, cantidad FROM producto WHERE cod_producto = %s FOR UPDATE", (cod_producto,))
                actual = cursor.fetchone()
                if actual is None:
                    raise ValueError(f"El producto {linea['producto']} ya no existe.")
                tipo, marca, precio, stock = actual
                if linea["cantidad"] > stock:
                    raise ValueError(f"Stock insuficiente: solo quedan {stock} unidades de {tipo} {marca}.")
                precios[cod_producto] = precio # SE COBRA EL PRECIO VIGENTE AL MOMENTO DE REGISTRAR
                total += precio * linea["cantidad"]
            cursor.execute("INSERT INTO venta (fecha, forma_pago, cod_cliente, total, cod_usuario) VALUES (CURDATE(), %s, %s, %s, %s)",
                           (pago, cliente[0], total, sesion.get("cod")))
            num_venta = cursor.lastrowid
            for cod_producto, linea in carrito.items():
                cursor.execute("INSERT INTO det_venta (num_venta, cod_producto, cantidad, precio_unitario) VALUES (%s, %s, %s, %s)",
                               (num_venta, cod_producto, linea["cantidad"], precios[cod_producto]))
                cursor.execute("UPDATE producto SET cantidad = cantidad - %s WHERE cod_producto = %s", (linea["cantidad"], cod_producto))
    except ValueError as e: # cursor_bd() YA HIZO ROLLBACK
        aviso(str(e), "No se pudo registrar")
        busca_productos_venta()
        return
    reinicia_venta()
    accion = pregunta_boleta(num_venta, cliente[1], total, None if recibido is None else recibido - total)
    if accion == "imprimir":
        imprime_boleta(num_venta)
    elif accion == "pdf":
        guarda_boleta(num_venta)
def pregunta_boleta(num_venta, cliente, total, vuelto): # DEVUELVE "imprimir", "pdf" O None
    caja = QMessageBox(ventana)
    caja.setWindowTitle("Venta registrada")
    caja.setIcon(QMessageBox.Icon.Information)
    caja.setText(f"Venta N° {num_venta} registrada.\nCliente: {cliente}\nTotal: {soles(total)}"
                 + (f"\nVuelto: {soles(vuelto)}" if vuelto is not None else ""))
    caja.setInformativeText("¿Qué deseas hacer con la boleta?")
    imprimir = caja.addButton("Imprimir boleta", QMessageBox.ButtonRole.AcceptRole)
    pdf = caja.addButton("Guardar PDF…", QMessageBox.ButtonRole.ActionRole)
    caja.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
    caja.setDefaultButton(imprimir)
    caja.exec()
    elegido = caja.clickedButton()
    return "imprimir" if elegido is imprimir else "pdf" if elegido is pdf else None
def elige_impresora(impresora): # DIALOGO DEL SISTEMA PARA ELEGIR LA IMPRESORA
    return QPrintDialog(impresora, ventana).exec() == QDialog.DialogCode.Accepted
def imprime_pdf(ruta): # SE IMPRIME EL MISMO PDF DE LA BOLETA, PAGINA POR PAGINA
    impresora = QPrinter(QPrinter.PrinterMode.HighResolution)
    impresora.setPageSize(QPageSize(QPageSize.PageSizeId.A5))
    if not elige_impresora(impresora):
        return False
    documento = QPdfDocument(None)
    documento.load(ruta)
    pintor = QPainter(impresora)
    for numero in range(documento.pageCount()):
        if numero:
            impresora.newPage()
        area, tamano = pintor.viewport(), documento.pagePointSize(numero)
        escala = min(area.width() / tamano.width(), area.height() / tamano.height())
        pintor.drawImage(0, 0, documento.render(numero, QSize(int(tamano.width() * escala), int(tamano.height() * escala))))
    pintor.end()
    documento.close()
    return True
def imprime_boleta(num_venta=None):
    num_venta = num_venta or ui.tabla_ventas.codigo_seleccionado()
    if num_venta is None:
        return
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, f"boleta_venta_{num_venta:06d}.pdf")
        genera_boleta(ruta, datos_venta(num_venta))
        if imprime_pdf(ruta):
            informa(f"Boleta de la venta N° {num_venta} enviada a la impresora.")
# HISTORIAL DE VENTAS
def busca_ventas():
    desde, hasta = ui.fecha_desde.date().toPyDate(), ui.fecha_hasta.date().toPyDate()
    texto, estado = ui.buscador_ventas.text().strip(), ui.cmb_estado_venta.currentData()
    elegido = ui.tabla_ventas.codigo_seleccionado()
    filas["ventas"] = [] if desde > hasta else bd.consulta(""" SELECT v.num_venta, v.fecha, COALESCE(c.nombre, 'Cliente varios'), COALESCE(u.nombre, '-'), v.forma_pago, v.total, v.estado
        FROM venta v
        LEFT JOIN cliente c ON c.cod_cliente = v.cod_cliente
        LEFT JOIN usuario u ON u.cod_usuario = v.cod_usuario
        WHERE v.fecha BETWEEN %s AND %s AND (%s IS NULL OR v.estado = %s)
          AND (%s = '' OR CAST(v.num_venta AS CHAR) = %s OR c.dni = %s OR COALESCE(c.nombre, 'Cliente varios') LIKE %s)
        ORDER BY v.num_venta DESC """, (desde, hasta, estado, estado, texto, texto, texto, patron_like(texto)))
    def celdas(datos): # PAGO Y VENDEDOR SE VEN EN EL DETALLE
        return [celda(datos[0], True), celda_fecha(datos[1]), celda(datos[2]), celda_soles(datos[5]),
                celda(datos[6].capitalize(), etiqueta="peligro" if datos[6] == "ANULADA" else "exito")]
    reconstruye_tabla(ui.tabla_ventas, filas["ventas"], celdas, elegido)
    registradas = [fila for fila in filas["ventas"] if fila[6] == "REGISTRADA"]
    if desde > hasta:
        ui.lbl_resumen_ventas.setText("La fecha «Desde» no puede ser posterior a «Hasta».")
    else:
        anuladas = len(filas["ventas"]) - len(registradas)
        ui.lbl_resumen_ventas.setText(f"{plural(len(filas['ventas']), 'venta')}  ·  Total vendido: {soles(sum((f[5] for f in registradas), Decimal('0')))}"
                                      + (f"  ·  {plural(anuladas, 'anulada')}" if anuladas else ""))
    muestra_detalle_venta()
def datos_venta(num_venta): # TODO LO NECESARIO PARA EL DETALLE Y LA BOLETA
    cabecera = bd.consulta_uno(""" SELECT v.num_venta, v.fecha, v.forma_pago, v.total, v.estado, v.motivo_anulacion, v.fecha_anulacion,
            COALESCE(c.nombre, 'Cliente varios'), c.dni, COALESCE(u.nombre, '-'), COALESCE(ua.nombre, '-')
        FROM venta v
        LEFT JOIN cliente c ON c.cod_cliente = v.cod_cliente
        LEFT JOIN usuario u ON u.cod_usuario = v.cod_usuario
        LEFT JOIN usuario ua ON ua.cod_usuario = v.cod_usuario_anula
        WHERE v.num_venta = %s """, (num_venta,))
    if cabecera is None:
        return None
    claves = ["num", "fecha", "forma_pago", "total", "estado", "motivo", "fecha_anulacion", "cliente", "dni", "vendedor", "anulada_por"]
    venta = dict(zip(claves, cabecera))
    venta["lineas"] = bd.consulta(""" SELECT CONCAT(p.tipo, ' ', p.marca), d.cantidad, d.precio_unitario
        FROM det_venta d INNER JOIN producto p ON p.cod_producto = d.cod_producto
        WHERE d.num_venta = %s ORDER BY p.tipo """, (num_venta,))
    return venta
def muestra_detalle_venta():
    num_venta = ui.tabla_ventas.codigo_seleccionado()
    venta = datos_venta(num_venta) if num_venta is not None else None
    ui.btn_boleta.setEnabled(venta is not None)
    ui.btn_imprimir.setEnabled(venta is not None)
    ui.btn_anular.setEnabled(venta is not None and venta["estado"] == "REGISTRADA" and puede("anular"))
    anulada = venta is not None and venta["estado"] == "ANULADA"
    ui.detalle_historial.limpia()
    ui.sello_anulada.setVisible(anulada)
    for widget in (ui.lbl_etiqueta_total_venta, *ui.separadores_detalle):
        widget.setVisible(venta is not None)
    ui.lbl_total_venta.setProperty("anulada", anulada) # EL TOTAL TACHADO: YA NO CUENTA EN LO VENDIDO
    interfaz.repule(ui.lbl_total_venta)
    if venta is None:
        ui.grupo_detalle_venta.setTitle("Detalle")
        ui.lbl_fecha_detalle.setText("")
        ui.lbl_info_venta.setText("") # EL ESTADO VACIO DEL DETALLE YA LO INDICA
        ui.lbl_total_venta.setText("")
        return
    ui.grupo_detalle_venta.setTitle(f"Venta N° {venta['num']}")
    ui.lbl_fecha_detalle.setText(f"{venta['fecha']:%d/%m/%Y}")
    dni = f" · DNI {venta['dni']}" if venta["dni"] else ""
    ui.lbl_info_venta.setText(f"<b>{escape(venta['cliente'])}</b>{dni}<br><span style='color:{interfaz.TEMA['texto_suave']}'>"
                              f"{venta['forma_pago'].capitalize()}  ·  Atendió: {escape(venta['vendedor'])}</span>")
    if anulada:
        ui.lbl_sello.setText(f"El {venta['fecha_anulacion']:%d/%m/%Y %H:%M} por {venta['anulada_por']}. Motivo: {venta['motivo'] or '-'}")
    for producto, cantidad, precio in venta["lineas"]:
        ui.detalle_historial.agrega(interfaz.LineaDetalle(producto, f"{cantidad} × {soles(precio)}", soles(cantidad * precio)))
    ui.lbl_total_venta.setText(soles(venta["total"]))
def anula_venta():
    if not puede("anular"):
        aviso("Solo un administrador puede anular ventas.", "Sin permiso")
        return
    num_venta = ui.tabla_ventas.codigo_seleccionado()
    venta = datos_venta(num_venta) if num_venta is not None else None
    if venta is None or venta["estado"] != "REGISTRADA":
        return
    motivo, aceptado = QInputDialog.getText(ventana, "Anular venta", f"Motivo de la anulación de la venta N° {num_venta}:")
    if not aceptado:
        return
    if not motivo.strip():
        aviso("Indica el motivo de la anulación.")
        return
    if not confirma(f"¿Anular la venta N° {num_venta} de {soles(venta['total'])} a {venta['cliente']}?\n"
                    "Se devolverá el stock de sus productos. Esta acción no se puede deshacer.", "Anular venta"):
        return
    try:
        with bd.cursor_bd() as cursor: # TODO O NADA: STOCK DEVUELTO Y VENTA MARCADA
            cursor.execute("SELECT estado FROM venta WHERE num_venta = %s FOR UPDATE", (num_venta,))
            if cursor.fetchone()[0] != "REGISTRADA":
                raise ValueError("La venta ya fue anulada por otro usuario.")
            cursor.execute(""" UPDATE producto p INNER JOIN det_venta d ON d.cod_producto = p.cod_producto
                SET p.cantidad = p.cantidad + d.cantidad WHERE d.num_venta = %s """, (num_venta,))
            cursor.execute(""" UPDATE venta SET estado = 'ANULADA', fecha_anulacion = NOW(), motivo_anulacion = %s, cod_usuario_anula = %s
                WHERE num_venta = %s """, (motivo.strip()[:255], sesion.get("cod"), num_venta))
    except ValueError as e:
        aviso(str(e), "No se pudo anular")
    busca_ventas()
    informa(f"Venta N° {num_venta} anulada. Se devolvió el stock de sus productos.")
def guarda_boleta(num_venta=None):
    num_venta = num_venta or ui.tabla_ventas.codigo_seleccionado()
    if num_venta is None:
        return
    ruta = pide_ruta("Guardar boleta", f"boleta_venta_{num_venta:06d}.pdf", "PDF (*.pdf)", ".pdf")
    if not ruta:
        return
    genera_boleta(ruta, datos_venta(num_venta))
    ofrece_abrir(ruta, "Boleta")
def genera_boleta(ruta, venta):
    estilos = getSampleStyleSheet()
    normal = ParagraphStyle("normal", parent=estilos["Normal"], fontSize=9, leading=12)
    pequeno = ParagraphStyle("pequeno", parent=normal, fontSize=7.5, textColor=colors.HexColor("#5f6773"))
    turquesa = colors.HexColor(interfaz.COLOR_PRIMARIO)
    datos = [["Cant.", "Descripción", "P. unit.", "Importe"]]
    for producto, cantidad, precio in venta["lineas"]:
        datos.append([str(cantidad), Paragraph(escape(producto), normal), soles(precio), soles(precio * cantidad)])
    datos.append(["", "", "TOTAL", soles(venta["total"])])
    tabla = Table(datos, colWidths=[1.3*cm, 5.5*cm, 2.4*cm, 2.6*cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), turquesa),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor("#c3c8cf")),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    contenido = [
        Paragraph("<b>LGD Technologies</b>", ParagraphStyle("marca", parent=estilos["Title"], fontSize=15, textColor=turquesa, spaceAfter=2)),
        Paragraph(f"<b>Boleta de venta N° {venta['num']:06d}</b>", ParagraphStyle("doc", parent=normal, fontSize=11, alignment=1)),
        Spacer(1, 0.4*cm),
        Paragraph(f"<b>Fecha:</b> {venta['fecha']:%d/%m/%Y}", normal),
        Paragraph(f"<b>Cliente:</b> {escape(venta['cliente'])}" + (f"  ·  <b>DNI:</b> {venta['dni']}" if venta["dni"] else ""), normal),
        Paragraph(f"<b>Forma de pago:</b> {venta['forma_pago']}  ·  <b>Atendido por:</b> {escape(venta['vendedor'])}", normal),
        Spacer(1, 0.3*cm),
        tabla,
    ]
    if venta["estado"] == "ANULADA":
        contenido += [Spacer(1, 0.4*cm), Paragraph(f"<b>VENTA ANULADA</b> el {venta['fecha_anulacion']:%d/%m/%Y}. Motivo: {escape(venta['motivo'] or '')}",
                                                   ParagraphStyle("anulada", parent=normal, textColor=colors.HexColor(interfaz.COLOR_PELIGRO), fontSize=10))]
    contenido += [Spacer(1, 0.6*cm), Paragraph("Gracias por su compra. Documento interno sin valor tributario.", pequeno)]
    SimpleDocTemplate(ruta, pagesize=A5, title=f"Boleta de venta {venta['num']:06d}", leftMargin=1.5*cm, rightMargin=1.5*cm,
                      topMargin=1.5*cm, bottomMargin=1.5*cm).build(contenido)
# REPORTES
ultimo_reporte = {} # DATOS DEL REPORTE EN PANTALLA, PARA EXPORTARLO A PDF O EXCEL
# CADA AGRUPACION: COLUMNAS (NOMBRE, TIPO), COLUMNA ANCHA, ANCHOS EN EL PDF (CM) Y EN EXCEL; LA ULTIMA COLUMNA SIEMPRE SE SUMA
AGRUPACIONES = {
    "ventas": {"columnas": [("N° venta", "numero"), ("Fecha", "fecha"), ("Productos", "texto"), ("Cliente", "texto"), ("Pago", "etiqueta"), ("Total", "soles")],
               "ancha": 2, "pdf": (1.7, 2.1, 5.9, 3.7, 1.8, 2.4), "excel": (10, 12, 48, 28, 10, 14), "titulo": "", "archivo": "", "fila": ("venta", "ventas")},
    "productos": {"columnas": [("Producto", "texto"), ("Unidades", "numero"), ("N° ventas", "numero"), ("Importe", "soles")],
                  "ancha": 0, "pdf": (8.6, 2.6, 2.6, 3.8), "excel": (40, 12, 12, 16), "titulo": " · por producto", "archivo": "_por_producto", "fila": ("producto", "productos")},
    "vendedores": {"columnas": [("Vendedor", "texto"), ("N° ventas", "numero"), ("Ticket promedio", "soles"), ("Total", "soles")],
                   "ancha": 0, "pdf": (7.6, 2.6, 3.6, 3.8), "excel": (34, 12, 18, 16), "titulo": " · por vendedor", "archivo": "_por_vendedor", "fila": ("vendedor", "vendedores")},
}
def abre_reportes(): # SE ACTUALIZA AL ENTRAR: SIEMPRE MUESTRA LAS VENTAS AL DIA
    genera_reporte()
def consulta_reporte(inicio, fin): # UNA FILA POR VENTA; LAS ANULADAS NO CUENTAN
    return bd.consulta(""" SELECT v.num_venta, v.fecha,
            GROUP_CONCAT(CONCAT(p.tipo, ' ', p.marca, ' x', d.cantidad) ORDER BY p.tipo SEPARATOR ', '),
            COALESCE(c.nombre, 'Cliente varios'), v.forma_pago, v.total
        FROM venta v
        LEFT JOIN cliente c ON v.cod_cliente = c.cod_cliente
        INNER JOIN det_venta d ON d.num_venta = v.num_venta
        INNER JOIN producto p ON d.cod_producto = p.cod_producto
        WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'REGISTRADA'
        GROUP BY v.num_venta, v.fecha, c.nombre, v.forma_pago, v.total
        ORDER BY v.fecha, v.num_venta """, (inicio, fin))
def consulta_agrupada(agrupacion, inicio, fin):
    if agrupacion == "productos": # LO MAS VENDIDO (EN SOLES) PRIMERO
        return bd.consulta(""" SELECT CONCAT(p.tipo, ' ', p.marca), SUM(d.cantidad), COUNT(DISTINCT v.num_venta), SUM(d.cantidad * d.precio_unitario)
            FROM det_venta d
            INNER JOIN venta v ON v.num_venta = d.num_venta
            INNER JOIN producto p ON p.cod_producto = d.cod_producto
            WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'REGISTRADA'
            GROUP BY p.cod_producto, p.tipo, p.marca
            ORDER BY 4 DESC, 1 """, (inicio, fin))
    return bd.consulta(""" SELECT COALESCE(u.nombre, '-'), COUNT(*), ROUND(AVG(v.total), 2), SUM(v.total)
        FROM venta v LEFT JOIN usuario u ON u.cod_usuario = v.cod_usuario
        WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'REGISTRADA'
        GROUP BY v.cod_usuario, u.nombre
        ORDER BY 4 DESC, 1 """, (inicio, fin))
def titulo_reporte(inicio, fin): # (TITULO, NOMBRE DE ARCHIVO) SEGUN EL PERIODO ELEGIDO
    if inicio == fin:
        return f"Reporte diario - {inicio:%d/%m/%Y}", f"reporte_diario_{inicio:%Y-%m-%d}"
    if inicio.day == 1 and (inicio.year, inicio.month) == (fin.year, fin.month) and fin.day == calendar.monthrange(fin.year, fin.month)[1]:
        return f"Reporte mensual - {MESES[inicio.month - 1]} {inicio.year}", f"reporte_mensual_{inicio:%Y-%m}"
    if inicio.weekday() == 0 and (fin - inicio).days == 6:
        return f"Reporte semanal - del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y}", f"reporte_semanal_{inicio:%Y-%m-%d}"
    return f"Reporte de ventas - del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y}", f"reporte_{inicio:%Y-%m-%d}_al_{fin:%Y-%m-%d}"
def genera_reporte(): # SE LLAMA SOLO AL CAMBIAR EL PERIODO O LA AGRUPACION
    inicio, fin = ui.periodo_reporte.fechas()
    agrupacion = ui.cmb_agrupar.currentData()
    ultimo_reporte.clear()
    if inicio > fin:
        muestra_reporte(agrupacion, None, [], "La fecha «Desde» no puede ser posterior a «Hasta».")
        return
    ventas = consulta_reporte(inicio, fin)
    datos = ventas if agrupacion == "ventas" else consulta_agrupada(agrupacion, inicio, fin)
    config = AGRUPACIONES[agrupacion]
    titulo, archivo = titulo_reporte(inicio, fin)
    ultimo_reporte.update({"titulo": titulo + config["titulo"], "archivo": archivo + config["archivo"], "periodo": f"{inicio:%d/%m/%Y} al {fin:%d/%m/%Y}",
                           "agrupacion": agrupacion, "columnas": config["columnas"], "filas": datos, "ventas": len(ventas),
                           "total": sum((fila[-1] for fila in datos), Decimal("0"))})
    muestra_reporte(agrupacion, (inicio, fin), ventas)
def celda_reporte(valor, tipo):
    if tipo == "soles":
        return celda_soles(valor)
    if tipo == "fecha":
        return celda_fecha(valor)
    return celda(valor, tipo == "numero", "neutro" if tipo == "etiqueta" else None)
def muestra_reporte(agrupacion, rango, ventas, error=None):
    config = AGRUPACIONES[agrupacion]
    columnas = config["columnas"]
    tabla = ui.tabla_reporte
    tabla.configura_columnas([nombre for nombre, _ in columnas], config["ancha"],
                             [numero for numero, (_, tipo) in enumerate(columnas) if tipo in ("numero", "soles")])
    tabla.mostrar_vacio(error or "No hay ventas en este periodo.")
    datos = ultimo_reporte.get("filas", [])
    reconstruye_tabla(tabla, datos, lambda fila: [celda_reporte(valor, tipo) for valor, (_, tipo) in zip(fila, columnas)])
    total = sum((venta[5] for venta in ventas), Decimal("0"))
    ui.cifra_ventas.valor.setText(str(len(ventas)))
    ui.cifra_total.valor.setText(soles(total))
    ui.cifra_promedio.valor.setText(soles(total / len(ventas)) if ventas else "-")
    ui.lbl_periodo.setText(ultimo_reporte.get("titulo", "Reporte de ventas"))
    ui.lbl_resumen.setText(error or f"Del {ultimo_reporte['periodo']}  ·  {plural(len(datos), *config['fila'])}")
    # EL GRAFICO SOLO TIENE SENTIDO CON MAS DE UN DIA; LOS PERIODOS LARGOS VAN POR MES
    dias = (rango[1] - rango[0]).days + 1 if rango else 0
    ui.muestra_grafico_reporte(dias > 1)
    if dias > 1:
        por_dia = {}
        for venta in ventas:
            total_dia, cantidad = por_dia.get(venta[1], (0, 0))
            por_dia[venta[1]] = (total_dia + venta[5], cantidad + 1)
        por_mes = dias > 62
        ui.grupo_grafico_reporte.setTitle("Ventas por mes" if por_mes else "Ventas por día")
        ui.grafico_reporte.muestra((barras_por_mes if por_mes else barras_por_dia)(rango[0], rango[1], por_dia))
    ui.btn_exportar_pdf.setEnabled(bool(datos))
    ui.btn_exportar_excel.setEnabled(bool(datos))
def exporta(extension):
    if not ultimo_reporte.get("filas"):
        return
    pdf = extension == ".pdf"
    ruta = pide_ruta("Guardar reporte", ultimo_reporte["archivo"] + extension, "PDF (*.pdf)" if pdf else "Excel (*.xlsx)", extension)
    if not ruta:
        return
    boton = ui.btn_exportar_pdf if pdf else ui.btn_exportar_excel
    boton.setEnabled(False) # EVITA DOBLE CLIC MIENTRAS SE GENERA
    try:
        (genera_pdf if pdf else genera_excel)(ruta, ultimo_reporte)
    finally:
        boton.setEnabled(True)
    ofrece_abrir(ruta, "Reporte")
def genera_pdf(ruta, reporte):
    estilos = getSampleStyleSheet()
    texto_celda = ParagraphStyle("celda", parent=estilos["Normal"], fontSize=9, leading=11)
    turquesa = colors.HexColor(interfaz.COLOR_PRIMARIO)
    columnas = reporte["columnas"]
    def valor_pdf(valor, tipo):
        if tipo == "soles":
            return soles(valor)
        if tipo == "fecha":
            return f"{valor:%d/%m/%Y}"
        return Paragraph(escape(str(valor)), texto_celda) if tipo == "texto" else str(valor)
    datos = [[nombre for nombre, _ in columnas]]
    for fila in reporte["filas"]:
        datos.append([valor_pdf(valor, tipo) for valor, (_, tipo) in zip(fila, columnas)])
    datos.append([""] * (len(columnas) - 2) + ["TOTAL", soles(reporte["total"])])
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), turquesa),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#f2f4f6")]),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#c3c8cf")),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    estilo += [('ALIGN', (numero, 0), (numero, -1), 'RIGHT') for numero, (_, tipo) in enumerate(columnas) if tipo in ("numero", "soles")]
    tabla = Table(datos, colWidths=[ancho * cm for ancho in AGRUPACIONES[reporte["agrupacion"]]["pdf"]], repeatRows=1)
    tabla.setStyle(TableStyle(estilo))
    contenido = [
        Paragraph(escape(reporte["titulo"]), estilos["Title"]),
        Paragraph(f"Periodo: del {reporte['periodo']}", estilos["Normal"]),
        Paragraph(f"{plural(reporte['ventas'], 'venta')} · Generado el {datetime.now():%d/%m/%Y %H:%M}", estilos["Normal"]),
        Spacer(1, 0.5*cm),
        tabla,
    ]
    SimpleDocTemplate(ruta, pagesize=letter, title=reporte["titulo"], leftMargin=2*cm, rightMargin=2*cm,
                      topMargin=2*cm, bottomMargin=2*cm).build(contenido)
def genera_excel(ruta, reporte):
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Ventas"
    hoja["A1"] = reporte["titulo"]
    hoja["A1"].font = Font(size=14, bold=True)
    hoja["A2"] = f"Periodo: del {reporte['periodo']}"
    hoja["A3"] = f"Generado el {datetime.now():%d/%m/%Y %H:%M}"
    columnas = reporte["columnas"]
    letras = "ABCDEF"[:len(columnas)]
    relleno = PatternFill("solid", fgColor=interfaz.COLOR_PRIMARIO.lstrip("#"))
    for columna, (texto, _) in enumerate(columnas, start=1):
        celda_excel = hoja.cell(row=5, column=columna, value=texto)
        celda_excel.font = Font(bold=True, color="FFFFFF")
        celda_excel.fill = relleno
        celda_excel.alignment = Alignment(horizontal="center")
    formato_soles = '"S/" #,##0.00'
    for fila, valores in enumerate(reporte["filas"], start=6): # FECHAS Y MONTOS COMO VALORES REALES, NO COMO TEXTO
        for columna, (valor, (_, tipo)) in enumerate(zip(valores, columnas), start=1):
            celda_excel = hoja.cell(row=fila, column=columna, value=valor)
            if tipo == "fecha":
                celda_excel.number_format = "DD/MM/YYYY"
            elif tipo == "soles":
                celda_excel.number_format = formato_soles
    ultima = 5 + len(reporte["filas"])
    hoja.cell(row=ultima + 1, column=len(columnas) - 1, value="TOTAL").font = Font(bold=True)
    total = hoja.cell(row=ultima + 1, column=len(columnas), value=f"=SUM({letras[-1]}6:{letras[-1]}{ultima})") # FORMULA: SE RECALCULA SI EDITAN EL ARCHIVO
    total.font = Font(bold=True)
    total.number_format = formato_soles
    for columna, ancho in zip(letras, AGRUPACIONES[reporte["agrupacion"]]["excel"]):
        hoja.column_dimensions[columna].width = ancho
    hoja.freeze_panes = "A6"
    hoja.auto_filter.ref = f"A5:{letras[-1]}{ultima}"
    libro.save(ruta)
# ERRORES
def mensaje_error(error):
    if isinstance(error, bd.ErrorConfiguracion):
        return str(error)
    if isinstance(error, pymysql.err.OperationalError):
        datos = bd.config or {}
        return (f"No se pudo conectar con MySQL ({datos.get('host')}:{datos.get('port')}, base {datos.get('database')}).\n"
                f"Verifica que el servidor esté encendido y los datos de config.ini.\n\nDetalle: {error.args[-1]}")
    return f"Ocurrió un error inesperado: {error}"
def maneja_error_inesperado(tipo, error, traza): # EN VEZ DE CERRAR LA APLICACION, AVISA Y GUARDA EL DETALLE
    logging.error("Error no controlado", exc_info=(tipo, error, traza))
    QMessageBox.critical(ventana, "Error", f"{mensaje_error(error)}\n\nEl detalle quedó registrado en {os.path.basename(ARCHIVO_LOG)}.")
def verifica_conexion():
    try:
        bd.consulta("SELECT 1")
    except (bd.ErrorConfiguracion, pymysql.err.MySQLError) as error:
        logging.error("Sin conexión a la base de datos", exc_info=True)
        QMessageBox.critical(None, "Sin conexión", mensaje_error(error))
        return False
    try: # LAS COLUMNAS MAS NUEVAS DEL ESQUEMA: SI FALTAN, LA BASE ES DE UNA VERSION ANTERIOR
        bd.consulta("SELECT debe_cambiar_clave FROM usuario LIMIT 0")
        return True
    except pymysql.err.MySQLError as error:
        if error.args[0] not in (1054, 1146): # COLUMNA O TABLA INEXISTENTE
            raise
        script = "BD/actualizar_bd.sql" if error.args[0] == 1146 else "BD/actualizar_bd_2.sql"
        QMessageBox.critical(None, "Base de datos desactualizada",
                             "La base de datos se creó con una versión anterior del sistema.\n"
                             f"Haz un respaldo y ejecuta una sola vez {script} "
                             "(ver «Actualizar una base de datos anterior» en el README).")
        return False
# INICIO
PAUSA_BUSQUEDA = 300 # MS QUE SE ESPERA TRAS LA ULTIMA TECLA ANTES DE BUSCAR
ATAJOS_MENU = ["inicio", "clientes", "productos", "venta", "ventas", "reportes", "usuarios"] # CTRL+1 ... CTRL+7
ajustes = None # QSettings: ULTIMO USUARIO, TAMAÑO DE LA VENTANA Y ULTIMA PANTALLA
atajos, temporizadores = {}, []
filtro_cierre = filtro_actividad = None
def configura_aplicacion(app, tema="claro"):
    interfaz.prepara_aplicacion(app, tema)
def crea_ventana():
    global ventana, ui, filtro_cierre, filtro_actividad, inactividad
    ventana = QMainWindow()
    ui = interfaz.Interfaz(ventana)
    if ajustes is not None and ajustes.value("ventana/geometria") is not None:
        ventana.restoreGeometry(ajustes.value("ventana/geometria"))
    filtro_cierre = FiltroCierre()
    ventana.installEventFilter(filtro_cierre)
    conecta_eventos()
    if ajustes is not None:
        ui.contrae_menu(ajustes.value("apariencia/menu_contraido", False, type=bool), animado=False)
    minutos = bd.minutos_bloqueo()
    if minutos:
        inactividad = QTimer(ventana)
        inactividad.setSingleShot(True)
        inactividad.setInterval(minutos * 60 * 1000)
        inactividad.timeout.connect(bloquea_por_inactividad)
        filtro_actividad = FiltroActividad()
        QApplication.instance().installEventFilter(filtro_actividad)
        QApplication.instance().aboutToQuit.connect(quita_filtro_actividad)
        atexit.register(quita_filtro_actividad)
    return ventana
def quita_filtro_actividad(): # ANTES DE QUE PYTHON TERMINE: SI QT LE SIGUE PASANDO EVENTOS AL CERRAR, LA APLICACION SE CAE
    app = QApplication.instance()
    if app is not None and filtro_actividad is not None:
        app.removeEventFilter(filtro_actividad)
def con_pausa(senal, funcion, campo=None): # BUSCA AL DEJAR DE ESCRIBIR, NO EN CADA TECLA; ENTER BUSCA AL INSTANTE
    temporizador = QTimer(ventana)
    temporizador.setSingleShot(True)
    temporizador.setInterval(PAUSA_BUSQUEDA)
    temporizador.timeout.connect(funcion)
    senal.connect(lambda *_: temporizador.start())
    if campo is not None:
        campo.returnPressed.connect(lambda: (temporizador.stop(), funcion()))
    temporizadores.append(temporizador)
def entidad_visible():
    return entidad_de_pagina(ui.paginas.currentWidget())
def enfoca_buscador(): # CTRL+F
    buscador = {ui.clientes: ui.clientes.buscador, ui.productos: ui.productos.buscador, ui.usuarios: ui.usuarios.buscador,
                ui.venta: ui.buscador_producto_venta, ui.ventas: ui.buscador_ventas}.get(ui.paginas.currentWidget())
    if buscador is not None:
        buscador.setFocus()
        buscador.selectAll()
def limpia_busqueda(): # ESC EN UN BUSCADOR BORRA LO ESCRITO
    campo = QApplication.focusWidget()
    if isinstance(campo, QLineEdit) and campo.isClearButtonEnabled() and campo.text():
        campo.clear()
def crea_atajo(tecla, funcion):
    atajo = QShortcut(QKeySequence(tecla), ventana)
    atajo.activated.connect(lambda: None if ui.bloqueada() else funcion())
    atajos[tecla] = atajo
def conecta_eventos(): # LAS SEÑALES SE CONECTAN UNA SOLA VEZ PARA NO REPETIR ACCIONES
    # MENU Y SESION
    NAVEGACION.clear()
    NAVEGACION.update({
        "inicio": (ui.btn_inicio, ui.inicio, abre_inicio, None),
        "clientes": (ui.btn_clientes, ui.clientes, lambda: abre_entidad("cliente"), "clientes"),
        "productos": (ui.btn_productos, ui.productos, lambda: abre_entidad("producto"), "productos"),
        "venta": (ui.btn_venta, ui.venta, abre_venta, "venta"),
        "ventas": (ui.btn_ventas, ui.ventas, busca_ventas, "ventas"),
        "reportes": (ui.btn_reportes, ui.reportes, abre_reportes, "reportes"),
        "usuarios": (ui.btn_usuarios, ui.usuarios, lambda: abre_entidad("usuario"), "usuarios"),
    })
    for nombre, (boton, *_) in NAVEGACION.items():
        boton.clicked.connect(lambda _marcado=False, n=nombre: muestra_pagina(n))
    ui.btn_cambiar_clave.clicked.connect(lambda: crea_dialogo_clave().exec())
    ui.btn_cerrar_sesion.clicked.connect(lambda: cierra_sesion())
    ui.btn_respaldo.clicked.connect(respalda)
    ui.btn_tema.clicked.connect(cambia_tema)
    ui.btn_contraer.clicked.connect(alterna_menu)
    ui.bloqueo.btn_desbloquear.clicked.connect(desbloquea)
    ui.bloqueo.btn_cerrar_sesion.clicked.connect(sale_del_bloqueo)
    # PANEL DE INICIO: CADA TARJETA Y LISTA LLEVA A SU DETALLE
    ui.tarjeta_hoy.pulsado.connect(lambda: abre_historial("Hoy"))
    ui.tarjeta_mes.pulsado.connect(lambda: abre_historial("Este mes"))
    ui.tarjeta_clientes.pulsado.connect(lambda: muestra_pagina("clientes"))
    ui.tarjeta_stock.pulsado.connect(lambda: abre_producto(solo_stock_bajo=True))
    ui.tabla_stock_bajo.itemClicked.connect(lambda item: abre_producto(ui.tabla_stock_bajo.codigo_en_fila(item.row()), True))
    ui.lista_mas_vendidos.elegida.connect(abre_producto)
    ui.grupo_dias.buttonClicked.connect(lambda *_: muestra_grafico_inicio())
    # CLIENTES, PRODUCTOS Y USUARIOS
    for entidad in ("cliente", "producto", "usuario"):
        p = pagina(entidad)
        con_pausa(p.buscador.textChanged, lambda e=entidad: busca(e), p.buscador)
        p.tabla.itemSelectionChanged.connect(lambda e=entidad: selecciona(e))
        p.btn_nuevo.clicked.connect(lambda _marcado=False, e=entidad: nuevo(e, preguntar=True))
        p.btn_guardar.clicked.connect(lambda _marcado=False, e=entidad: guardar(e))
        p.btn_eliminar.clicked.connect(lambda _marcado=False, e=entidad: eliminar(e))
        p.btn_nuevo.setToolTip("Nuevo registro (Ctrl+N)")
        p.btn_guardar.setToolTip("Guardar (Ctrl+S o Enter)")
        p.buscador.setToolTip("Buscar (Ctrl+F) · Esc borra la búsqueda")
        for campo in p.campos.values():
            if hasattr(campo, "returnPressed") and campo is not p.campos["codigo"]: # ENTER EN EL FORMULARIO = GUARDAR
                campo.returnPressed.connect(lambda e=entidad: guardar(e))
    ui.chk_stock_bajo.toggled.connect(lambda *_: busca("producto"))
    ui.btn_ver_compras.clicked.connect(ver_compras_cliente)
    # VENTA
    con_pausa(ui.buscador_cliente_venta.textChanged, busca_clientes_venta, ui.buscador_cliente_venta)
    con_pausa(ui.buscador_producto_venta.textChanged, busca_productos_venta)
    ui.buscador_producto_venta.returnPressed.connect(agrega_por_codigo) # ENTER O LECTOR DE CODIGO = AGREGAR
    ui.btn_cliente_varios.clicked.connect(elige_cliente_varios)
    ui.btn_nuevo_cliente.clicked.connect(lambda: crea_dialogo_cliente().exec())
    ui.grupo_pago.buttonToggled.connect(lambda *_: actualiza_totales())
    ui.txt_recibido.textChanged.connect(actualiza_totales)
    ui.tabla_clientes_venta.itemSelectionChanged.connect(selecciona_cliente_venta)
    ui.tabla_productos_venta.itemSelectionChanged.connect(actualiza_disponible)
    ui.tabla_productos_venta.itemDoubleClicked.connect(agrega_producto) # DOBLE CLIC = AGREGAR
    ui.spn_cantidad.lineEdit().returnPressed.connect(agrega_producto) # ENTER EN CANTIDAD = AGREGAR
    ui.btn_agregar.clicked.connect(agrega_producto)
    ui.btn_cancelar_venta.clicked.connect(cancela_venta)
    ui.btn_registrar_venta.clicked.connect(registra_venta)
    # HISTORIAL
    ui.periodo_ventas.cambio.connect(busca_ventas)
    ui.cmb_estado_venta.currentIndexChanged.connect(busca_ventas)
    con_pausa(ui.buscador_ventas.textChanged, busca_ventas, ui.buscador_ventas)
    ui.tabla_ventas.itemSelectionChanged.connect(muestra_detalle_venta)
    ui.btn_boleta.clicked.connect(lambda: guarda_boleta())
    ui.btn_imprimir.clicked.connect(lambda: imprime_boleta())
    ui.btn_stock.clicked.connect(abre_dialogo_stock)
    ui.btn_anular.clicked.connect(anula_venta)
    # REPORTES
    ui.periodo_reporte.cambio.connect(genera_reporte)
    ui.cmb_agrupar.currentIndexChanged.connect(genera_reporte)
    ui.btn_exportar_pdf.clicked.connect(lambda: exporta(".pdf"))
    ui.btn_exportar_excel.clicked.connect(lambda: exporta(".xlsx"))
    # ATAJOS DE TECLADO
    for numero, nombre in enumerate(ATAJOS_MENU, start=1):
        boton = NAVEGACION[nombre][0]
        boton.setToolTip(f"Ctrl+{numero}")
        crea_atajo(f"Ctrl+{numero}", lambda n=nombre: NAVEGACION[n][0].isVisible() and muestra_pagina(n))
    crea_atajo("F2", lambda: puede("venta") and muestra_pagina("venta"))
    crea_atajo("Ctrl+F", enfoca_buscador)
    crea_atajo("Ctrl+N", lambda: entidad_visible() and nuevo(entidad_visible(), preguntar=True))
    crea_atajo("Ctrl+S", lambda: entidad_visible() and guardar(entidad_visible()))
    crea_atajo("Esc", limpia_busqueda)
ventana = ui = None
if __name__ == "__main__":
    logging.basicConfig(handlers=[logging.FileHandler(ARCHIVO_LOG, encoding="utf-8", delay=True)], # EL ARCHIVO SE CREA SOLO SI HAY ERRORES
                        level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    ajustes = QSettings("LGD Technologies", "Sistema de Ventas")
    configura_aplicacion(app, ajustes.value("apariencia/tema", "claro"))
    sys.excepthook = maneja_error_inesperado
    if not verifica_conexion():
        sys.exit(1)
    if not pide_login(): # CANCELAR EL INGRESO NO ES UN ERROR
        sys.exit(0)
    crea_ventana()
    aplica_sesion()
    ventana.show()
    sys.exit(app.exec())
