import sys
import os
import logging
import calendar
from decimal import Decimal
from datetime import date, datetime
from xml.sax.saxutils import escape
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QFileDialog, QInputDialog, QDialog, QCheckBox
from PyQt6.QtGui import QColor, QDesktopServices
from PyQt6.QtCore import Qt, QUrl, QStandardPaths, QTimer
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
# QUE PUEDE HACER CADA ROL (SE APLICA AL MENU Y TAMBIEN DENTRO DE CADA ACCION)
PERMISOS = {
    "ADMIN": {"clientes", "productos", "venta", "ventas", "reportes", "usuarios", "eliminar_cliente", "anular"},
    "VENDEDOR": {"clientes", "venta", "ventas"},
}

# CONSULTAS POR ENTIDAD. SIEMPRE PARAMETRIZADAS (%s): LOS DATOS VIAJAN APARTE DEL SQL, ASI NO HAY INYECCION
ENTIDADES = {
    "cliente": {
        "titulo": "Cliente", "articulo": "al cliente", "plural": "clientes",
        "busca": """ SELECT cod_cliente, nombre, dni, telefono, sexo FROM cliente
            WHERE CAST(cod_cliente AS CHAR) = %s OR nombre LIKE %s OR dni LIKE %s ORDER BY cod_cliente """,
        "registra": "INSERT INTO cliente (nombre, dni, telefono, sexo) VALUES (%s, %s, %s, %s)",
        "actualiza": "UPDATE cliente SET nombre = %s, dni = %s, telefono = %s, sexo = %s WHERE cod_cliente = %s",
        "elimina": "DELETE FROM cliente WHERE cod_cliente = %s",
    },
    "producto": {
        "titulo": "Producto", "articulo": "el producto", "plural": "productos",
        "busca": """ SELECT cod_producto, tipo, marca, precio, cantidad FROM producto
            WHERE CAST(cod_producto AS CHAR) = %s OR tipo LIKE %s OR marca LIKE %s ORDER BY cod_producto """,
        "registra": "INSERT INTO producto (tipo, marca, precio, cantidad) VALUES (%s, %s, %s, %s)",
        "actualiza": "UPDATE producto SET tipo = %s, marca = %s, precio = %s, cantidad = %s WHERE cod_producto = %s",
        "elimina": "DELETE FROM producto WHERE cod_producto = %s",
    },
    "usuario": {
        "titulo": "Usuario", "articulo": "al usuario", "plural": "usuarios",
        "busca": """ SELECT cod_usuario, usuario, nombre, rol, activo FROM usuario
            WHERE CAST(cod_usuario AS CHAR) = %s OR usuario LIKE %s OR nombre LIKE %s ORDER BY cod_usuario """,
        "registra": "INSERT INTO usuario (usuario, nombre, rol, activo, clave) VALUES (%s, %s, %s, %s, %s)",
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
def puede(permiso):
    return permiso in PERMISOS.get(sesion.get("rol"), set())
def aviso(texto, titulo="Revisa los datos"):
    QMessageBox.warning(ventana, titulo, texto)
def confirma(texto, titulo="Confirmar"):
    respuesta = QMessageBox.question(ventana, titulo, texto, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
    return respuesta == QMessageBox.StandardButton.Yes
def informa(texto):
    ui.barra_estado.showMessage(texto, 8000) # MENSAJE QUE NO INTERRUMPE
def patron_like(texto): # BUSQUEDA LITERAL: % Y _ ESCRITOS POR EL USUARIO NO SON COMODINES
    return "%" + texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
def celda(texto, numero=False, color=None):
    item = QTableWidgetItem(str(texto))
    if numero:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if color:
        item.setForeground(QColor(color))
    return item
def fila_seleccionada(tabla):
    seleccion = tabla.selectionModel().selectedRows()
    return seleccion[0].row() if seleccion else None
def reconstruye_tabla(tabla, datos, celdas, codigo_elegido=None):
    # AL FILTRAR, QT DEJA MARCADA LA FILA QUE QUEDA EN LA MISMA POSICION AUNQUE SEA OTRO REGISTRO.
    # SE LIMPIA LA SELECCION Y SOLO SE VUELVE A MARCAR EL REGISTRO ELEGIDO (POR CODIGO), SIN DISPARAR EVENTOS
    tabla.blockSignals(True)
    tabla.clearSelection()
    tabla.setRowCount(len(datos))
    for fila, registro in enumerate(datos):
        for columna, item in enumerate(celdas(registro)):
            tabla.setItem(fila, columna, item)
    tabla.clearSelection()
    tabla.setCurrentItem(None)
    for fila, registro in enumerate(datos):
        if registro[0] == codigo_elegido:
            tabla.selectRow(fila)
    tabla.blockSignals(False)
def codigo_seleccionado(tabla, datos):
    fila = fila_seleccionada(tabla)
    return None if fila is None or fila >= len(datos) else datos[fila][0]
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
def campos_faltantes(campos, obligatorios):
    faltan = [(nombre, campos[clave]) for clave, nombre in obligatorios
              if (campos[clave].currentData() is None if hasattr(campos[clave], "currentData") else campos[clave].text().strip() == "")]
    if faltan:
        return f"Completa: {', '.join(nombre for nombre, _ in faltan)}.", faltan[0][1]
    return None
def valida(entidad, codigo_actual):
    # DEVUELVE (MENSAJE, CAMPO) DEL PRIMER PROBLEMA, O None SI TODO ESTA BIEN
    campos = pagina(entidad).campos
    if entidad == "cliente":
        error = campos_faltantes(campos, (("nombre", "Nombre"), ("dni", "DNI"), ("telefono", "Teléfono"), ("sexo", "Sexo")))
        if error:
            return error
        dni, telefono = campos["dni"].text(), campos["telefono"].text()
        if not (dni.isdigit() and len(dni) == 8):
            return "El DNI debe tener 8 dígitos.", campos["dni"]
        if not (telefono.isdigit() and len(telefono) == 9):
            return "El teléfono debe tener 9 dígitos.", campos["telefono"]
        repetido = bd.consulta_uno("SELECT nombre FROM cliente WHERE dni = %s AND cod_cliente <> %s", (dni, codigo_actual or 0))
        if repetido:
            return f"El DNI {dni} ya está registrado para {repetido[0]}.", campos["dni"]
        return None
    if entidad == "producto":
        error = campos_faltantes(campos, (("tipo", "Tipo"), ("marca", "Marca"), ("precio", "Precio")))
        if error:
            return error
        if precio_numero(campos["precio"].text()) is None:
            return "El precio debe ser un número mayor o igual a 0.", campos["precio"]
        return None
    obligatorios = [("usuario", "Usuario"), ("nombre", "Nombre"), ("rol", "Rol")] + ([] if codigo_actual else [("clave", "Contraseña")])
    error = campos_faltantes(campos, obligatorios)
    if error:
        return error
    usuario = campos["usuario"].text().strip().lower()
    if bd.consulta_uno("SELECT 1 FROM usuario WHERE usuario = %s AND cod_usuario <> %s", (usuario, codigo_actual or 0)):
        return f"El usuario {usuario} ya existe.", campos["usuario"]
    if campos["clave"].text() and len(campos["clave"].text()) < seguridad.LARGO_MINIMO:
        return f"La contraseña debe tener al menos {seguridad.LARGO_MINIMO} caracteres.", campos["clave"]
    if codigo_actual == sesion.get("cod") and (campos["rol"].currentData() != "ADMIN" or not campos["activo"].isChecked()):
        return "No puedes quitarte el rol de administrador ni desactivar tu propio usuario.", campos["rol"]
    return None
def datos_formulario(entidad): # VALORES LISTOS PARA LA BD, SIN EL CODIGO
    campos = pagina(entidad).campos
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
def pagina(entidad):
    return {"cliente": ui.clientes, "producto": ui.productos, "usuario": ui.usuarios}[entidad]
def muestra_pagina(boton, widget, al_abrir=None, permiso=None):
    if permiso and not puede(permiso):
        aviso("Tu usuario no tiene permiso para esta opción.", "Sin permiso")
        return
    boton.setChecked(True)
    ui.paginas.setCurrentWidget(widget)
    if al_abrir:
        al_abrir()
def autentica(usuario, clave): # DEVUELVE (DATOS DE SESION, None) O (None, MENSAJE)
    fila = bd.consulta_uno("SELECT cod_usuario, usuario, nombre, rol, activo, clave FROM usuario WHERE usuario = %s", (usuario.strip().lower(),))
    if fila is None or not seguridad.verifica_clave(clave, fila[5]):
        return None, "Usuario o contraseña incorrectos." # NO SE DICE CUAL DE LOS DOS FALLO
    if not fila[4]:
        return None, "Tu usuario está desactivado. Consulta con el administrador."
    return {"cod": fila[0], "usuario": fila[1], "nombre": fila[2], "rol": fila[3]}, None
def crea_dialogo_login():
    dialogo = interfaz.DialogoLogin()
    fallos = [0]
    def desbloquea():
        fallos[0] = 0
        dialogo.btn_ingresar.setEnabled(True)
        dialogo.lbl_error.setText("")
    def ingresar():
        datos, error = autentica(dialogo.txt_usuario.text(), dialogo.txt_clave.text())
        if datos:
            sesion.clear()
            sesion.update(datos)
            dialogo.accept()
            return
        fallos[0] += 1
        dialogo.txt_clave.clear()
        dialogo.txt_clave.setFocus()
        if fallos[0] >= MAX_INTENTOS:
            dialogo.btn_ingresar.setEnabled(False)
            dialogo.lbl_error.setText(f"Demasiados intentos fallidos. Espera {ESPERA_BLOQUEO} segundos.")
            QTimer.singleShot(ESPERA_BLOQUEO * 1000, desbloquea)
        else:
            dialogo.lbl_error.setText(error)
    dialogo.btn_ingresar.clicked.connect(ingresar)
    return dialogo
def pide_login():
    return crea_dialogo_login().exec() == QDialog.DialogCode.Accepted
def aplica_sesion(): # MUESTRA SOLO LO QUE EL ROL PUEDE USAR Y DEJA TODO LIMPIO
    ui.lbl_sesion.setText(f"{sesion['nombre']}\n{sesion['usuario']} · {ROLES[sesion['rol']]}")
    for boton, permiso in ((ui.btn_productos, "productos"), (ui.btn_reportes, "reportes"), (ui.btn_usuarios, "usuarios")):
        boton.setVisible(puede(permiso))
    ui.clientes.btn_eliminar.setVisible(puede("eliminar_cliente"))
    ui.btn_anular.setVisible(puede("anular"))
    for entidad in en_edicion:
        en_edicion[entidad] = None
        pagina(entidad).buscador.clear()
    venta_actual["cliente"], venta_actual["carrito"] = None, {}
    ultimo_reporte.clear()
    muestra_pagina(ui.btn_inicio, ui.inicio, abre_inicio)
def cierra_sesion():
    if venta_actual["carrito"] and not confirma("Hay una venta en curso. ¿Cerrar sesión de todos modos?"):
        return
    ventana.hide()
    sesion.clear()
    if pide_login():
        aplica_sesion()
        ventana.show()
    else:
        QApplication.quit()
def crea_dialogo_clave():
    dialogo = interfaz.DialogoClave(ventana)
    def guardar():
        actual, nueva, repite = dialogo.txt_actual.text(), dialogo.txt_nueva.text(), dialogo.txt_repite.text()
        fila = bd.consulta_uno("SELECT clave FROM usuario WHERE cod_usuario = %s", (sesion["cod"],))
        if fila is None or not seguridad.verifica_clave(actual, fila[0]):
            dialogo.lbl_error.setText("La contraseña actual no es correcta.")
        elif len(nueva) < seguridad.LARGO_MINIMO:
            dialogo.lbl_error.setText(f"La nueva contraseña debe tener al menos {seguridad.LARGO_MINIMO} caracteres.")
        elif nueva != repite:
            dialogo.lbl_error.setText("Las contraseñas nuevas no coinciden.")
        elif nueva == actual:
            dialogo.lbl_error.setText("La nueva contraseña debe ser distinta de la actual.")
        else:
            bd.ejecuta("UPDATE usuario SET clave = %s WHERE cod_usuario = %s", (seguridad.cifra_clave(nueva), sesion["cod"]))
            dialogo.accept()
            informa("Contraseña actualizada.")
    dialogo.btn_guardar.clicked.connect(guardar)
    return dialogo
# PANEL DE INICIO
def abre_inicio():
    hoy = date.today()
    inicio_mes, fin_mes = date(hoy.year, hoy.month, 1), date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
    ui.lbl_saludo.setText(f"Hola, {sesion.get('nombre', '')}")
    ui.lbl_fecha_hoy.setText(f"{DIAS[hoy.weekday()].capitalize()} {hoy.day} de {MESES[hoy.month - 1].lower()} de {hoy.year}")
    resumen = """ SELECT COUNT(*), COALESCE(SUM(total), 0) FROM venta WHERE estado = 'REGISTRADA' AND fecha BETWEEN %s AND %s """
    for tarjeta, (inicio, fin) in ((ui.tarjeta_hoy, (hoy, hoy)), (ui.tarjeta_mes, (inicio_mes, fin_mes))):
        cantidad, total = bd.consulta_uno(resumen, (inicio, fin))
        tarjeta.valor.setText(soles(total))
        tarjeta.detalle.setText(f"{cantidad} venta{'s' if cantidad != 1 else ''}")
    ui.tarjeta_clientes.valor.setText(str(bd.consulta_uno("SELECT COUNT(*) FROM cliente")[0]))
    ui.tarjeta_clientes.detalle.setText("en total")
    stock_bajo = bd.consulta("SELECT cod_producto, CONCAT(tipo, ' ', marca), cantidad FROM producto WHERE cantidad <= %s ORDER BY cantidad, tipo", (STOCK_BAJO,))
    ui.tarjeta_stock.valor.setText(str(len(stock_bajo)))
    ui.tarjeta_stock.detalle.setText("con 5 unidades o menos" if stock_bajo else "Todo el stock está en orden")
    reconstruye_tabla(ui.tabla_stock_bajo, stock_bajo,
                      lambda datos: [celda(datos[1]), celda(datos[2], True, interfaz.COLOR_PELIGRO if datos[2] == 0 else None)])
    mas_vendidos = bd.consulta(""" SELECT p.cod_producto, CONCAT(p.tipo, ' ', p.marca), SUM(d.cantidad), SUM(d.cantidad * d.precio_unitario)
        FROM det_venta d
        INNER JOIN venta v ON v.num_venta = d.num_venta
        INNER JOIN producto p ON p.cod_producto = d.cod_producto
        WHERE v.estado = 'REGISTRADA' AND v.fecha BETWEEN %s AND %s
        GROUP BY p.cod_producto, p.tipo, p.marca
        ORDER BY 3 DESC, 4 DESC LIMIT 5 """, (inicio_mes, fin_mes))
    reconstruye_tabla(ui.tabla_mas_vendidos, mas_vendidos,
                      lambda datos: [celda(datos[1]), celda(datos[2], True), celda(soles(datos[3]), True)])
# CLIENTES, PRODUCTOS Y USUARIOS (MISMA PANTALLA: TABLA + FORMULARIO)
def abre_entidad(entidad):
    busca(entidad)
    if en_edicion[entidad] is None:
        nuevo(entidad)
    else:
        selecciona_codigo(entidad, en_edicion[entidad][0])
def busca(entidad):
    p = pagina(entidad)
    filas[entidad] = consulta_busqueda(entidad, p.buscador.text())
    def celdas(datos):
        if entidad == "cliente":
            return [celda(datos[0], True), celda(datos[1]), celda(datos[2]), celda(datos[3]), celda(datos[4].capitalize())]
        if entidad == "producto":
            return [celda(datos[0], True), celda(datos[1]), celda(datos[2]), celda(soles(datos[3]), True),
                    celda(datos[4], True, interfaz.COLOR_PELIGRO if datos[4] == 0 else None)] # SIN STOCK EN ROJO
        return [celda(datos[0], True), celda(datos[1]), celda(datos[2]), celda(ROLES[datos[3]]),
                celda("Sí" if datos[4] else "No", color=None if datos[4] else interfaz.COLOR_PELIGRO)]
    reconstruye_tabla(p.tabla, filas[entidad], celdas, en_edicion[entidad][0] if en_edicion[entidad] else None)
    total = len(filas[entidad])
    p.lbl_conteo.setText(f"{total} {ENTIDADES[entidad]['plural'] if total != 1 else entidad}")
def nuevo(entidad):
    p = pagina(entidad)
    en_edicion[entidad] = None
    p.tabla.clearSelection()
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
    p.grupo.setTitle(f"Nuevo {entidad}")
    p.btn_guardar.setText(f"Registrar {entidad}")
    p.btn_eliminar.setEnabled(False)
def selecciona(entidad): # AL ELEGIR UNA FILA, SUS DATOS PASAN AL FORMULARIO PARA EDITARLOS
    p = pagina(entidad)
    fila = fila_seleccionada(p.tabla)
    if fila is None:
        return
    datos = filas[entidad][fila]
    en_edicion[entidad] = datos
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
    else:
        campos["usuario"].setText(datos[1])
        campos["nombre"].setText(datos[2])
        campos["rol"].setCurrentIndex(max(campos["rol"].findData(datos[3]), 0))
        campos["activo"].setChecked(bool(datos[4]))
        campos["clave"].clear()
        campos["clave"].setPlaceholderText("Déjala vacía para no cambiarla")
    p.grupo.setTitle(f"Editar {entidad} N° {datos[0]}")
    p.btn_guardar.setText("Guardar cambios")
    p.btn_eliminar.setEnabled(True)
def selecciona_codigo(entidad, codigo): # MARCA EL REGISTRO Y CARGA EN EL FORMULARIO SUS DATOS ACTUALES
    for fila, datos in enumerate(filas[entidad]):
        if datos[0] == codigo:
            pagina(entidad).tabla.selectRow(fila)
            selecciona(entidad)
            return
    nuevo(entidad) # YA NO APARECE CON EL FILTRO ACTUAL
def guardar(entidad):
    datos_actuales = en_edicion[entidad]
    codigo = datos_actuales[0] if datos_actuales else None
    error = valida(entidad, codigo)
    if error:
        mensaje, campo = error
        aviso(mensaje)
        campo.setFocus()
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
            cursor.execute(ENTIDADES[entidad]["actualiza"], datos + (codigo,))
            if clave: # SOLO SI SE ESCRIBIO UNA NUEVA
                cursor.execute("UPDATE usuario SET clave = %s WHERE cod_usuario = %s", (seguridad.cifra_clave(clave), codigo))
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
# VENTA
venta_actual = {"cliente": None, "carrito": {}} # carrito: cod_producto -> {producto, precio, cantidad}
def abre_venta():
    busca_clientes_venta()
    busca_productos_venta()
    ui.lbl_num_venta.setText(f"Venta N° {bd.siguiente_codigo('venta')}  ·  {date.today():%d/%m/%Y}")
    muestra_cliente_venta()
    muestra_carrito()
def busca_clientes_venta():
    filas["venta_cliente"] = consulta_busqueda("cliente", ui.buscador_cliente_venta.text())
    cliente = venta_actual["cliente"]
    reconstruye_tabla(ui.tabla_clientes_venta, filas["venta_cliente"],
                      lambda datos: [celda(datos[0], True), celda(datos[1]), celda(datos[2])], cliente[0] if cliente else None)
def busca_productos_venta():
    elegido = codigo_seleccionado(ui.tabla_productos_venta, filas["venta_producto"])
    filas["venta_producto"] = consulta_busqueda("producto", ui.buscador_producto_venta.text())
    reconstruye_tabla(ui.tabla_productos_venta, filas["venta_producto"],
                      lambda datos: [celda(datos[0], True), celda(datos[1]), celda(datos[2]), celda(soles(datos[3]), True),
                                     celda(datos[4], True, interfaz.COLOR_PELIGRO if datos[4] == 0 else None)], elegido)
    actualiza_disponible()
def selecciona_cliente_venta():
    fila = fila_seleccionada(ui.tabla_clientes_venta)
    if fila is not None:
        codigo, nombre, dni, _, _ = filas["venta_cliente"][fila]
        venta_actual["cliente"] = (codigo, nombre, dni)
    muestra_cliente_venta()
def muestra_cliente_venta():
    cliente = venta_actual["cliente"]
    ui.lbl_cliente_venta.setText(f"Cliente: <b>{escape(cliente[1])}</b> (DNI {cliente[2]})" if cliente else "Cliente: <i>ninguno seleccionado</i>")
    actualiza_botones_venta()
def producto_venta_seleccionado():
    fila = fila_seleccionada(ui.tabla_productos_venta)
    return None if fila is None else filas["venta_producto"][fila]
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
        return
    codigo = producto[0]
    actual = bd.consulta_uno("SELECT tipo, marca, precio, cantidad FROM producto WHERE cod_producto = %s", (codigo,))
    if actual is None:
        aviso("El producto ya no existe.")
        busca_productos_venta()
        return
    tipo, marca, precio, stock = actual
    en_carrito = venta_actual["carrito"].get(codigo, {}).get("cantidad", 0)
    cantidad = en_carrito + ui.spn_cantidad.value()
    if cantidad > stock:
        aviso(f"Solo quedan {stock} unidades de {tipo} {marca}." + (f" Ya tienes {en_carrito} en esta venta." if en_carrito else ""), "Stock insuficiente")
        return
    venta_actual["carrito"][codigo] = {"producto": f"{tipo} {marca}", "precio": precio, "cantidad": cantidad}
    ui.spn_cantidad.setValue(1)
    muestra_carrito()
def quita_producto():
    fila = fila_seleccionada(ui.tabla_carrito)
    if fila is None:
        aviso("Selecciona en el detalle el producto que quieres quitar.")
        return
    codigo = list(venta_actual["carrito"])[fila]
    del venta_actual["carrito"][codigo]
    muestra_carrito()
def total_carrito():
    return sum((linea["precio"] * linea["cantidad"] for linea in venta_actual["carrito"].values()), Decimal("0"))
def muestra_carrito():
    tabla = ui.tabla_carrito
    tabla.setRowCount(len(venta_actual["carrito"]))
    for fila, linea in enumerate(venta_actual["carrito"].values()):
        tabla.setItem(fila, 0, celda(linea["producto"]))
        tabla.item(fila, 0).setToolTip(linea["producto"]) # NOMBRE COMPLETO SI LA COLUMNA LO CORTA
        tabla.setItem(fila, 1, celda(linea["cantidad"], True))
        tabla.setItem(fila, 2, celda(soles(linea["precio"]), True))
        tabla.setItem(fila, 3, celda(soles(linea["precio"] * linea["cantidad"]), True))
    ui.lbl_total.setText(f"Total: {soles(total_carrito())}")
    actualiza_disponible()
    actualiza_botones_venta()
def actualiza_botones_venta():
    hay_productos = bool(venta_actual["carrito"])
    ui.btn_registrar_venta.setEnabled(hay_productos and venta_actual["cliente"] is not None)
    ui.btn_registrar_venta.setToolTip("" if venta_actual["cliente"] else "Primero elige el cliente")
    ui.btn_quitar.setEnabled(hay_productos)
    ui.btn_cancelar_venta.setEnabled(hay_productos or venta_actual["cliente"] is not None)
def reinicia_venta():
    venta_actual["cliente"] = None
    venta_actual["carrito"] = {}
    ui.buscador_cliente_venta.clear()
    ui.buscador_producto_venta.clear()
    ui.cmb_forma_pago.setCurrentIndex(0)
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
    forma_pago = ui.cmb_forma_pago.currentText()
    if not confirma(f"¿Registrar la venta de {soles(total_carrito())} a {cliente[1]} ({forma_pago.lower()})?", "Registrar venta"):
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
                           (forma_pago, cliente[0], total, sesion.get("cod")))
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
    if confirma(f"Venta N° {num_venta} registrada.\nCliente: {cliente[1]}\nTotal: {soles(total)}\n\n¿Deseas guardar la boleta en PDF?", "Venta registrada"):
        guarda_boleta(num_venta)
# HISTORIAL DE VENTAS
def busca_ventas():
    desde, hasta = ui.fecha_desde.date().toPyDate(), ui.fecha_hasta.date().toPyDate()
    texto, estado = ui.buscador_ventas.text().strip(), ui.cmb_estado_venta.currentData()
    elegido = codigo_seleccionado(ui.tabla_ventas, filas["ventas"])
    filas["ventas"] = [] if desde > hasta else bd.consulta(""" SELECT v.num_venta, v.fecha, c.nombre, COALESCE(u.nombre, '-'), v.forma_pago, v.total, v.estado
        FROM venta v
        INNER JOIN cliente c ON c.cod_cliente = v.cod_cliente
        LEFT JOIN usuario u ON u.cod_usuario = v.cod_usuario
        WHERE v.fecha BETWEEN %s AND %s AND (%s IS NULL OR v.estado = %s)
          AND (%s = '' OR CAST(v.num_venta AS CHAR) = %s OR c.nombre LIKE %s)
        ORDER BY v.num_venta DESC """, (desde, hasta, estado, estado, texto, texto, patron_like(texto)))
    def celdas(datos):
        color = interfaz.COLOR_PELIGRO if datos[6] == "ANULADA" else None
        return [celda(datos[0], True), celda(f"{datos[1]:%d/%m/%Y}"), celda(datos[2]), celda(datos[3]), celda(datos[4]),
                celda(soles(datos[5]), True, color), celda(datos[6].capitalize(), color=color)]
    reconstruye_tabla(ui.tabla_ventas, filas["ventas"], celdas, elegido)
    registradas = [fila for fila in filas["ventas"] if fila[6] == "REGISTRADA"]
    if desde > hasta:
        ui.lbl_resumen_ventas.setText("La fecha «Desde» no puede ser posterior a «Hasta».")
    else:
        anuladas = len(filas["ventas"]) - len(registradas)
        ui.lbl_resumen_ventas.setText(f"{len(filas['ventas'])} ventas  ·  Total vendido: {soles(sum((f[5] for f in registradas), Decimal('0')))}"
                                      + (f"  ·  {anuladas} anuladas" if anuladas else ""))
    muestra_detalle_venta()
def datos_venta(num_venta): # TODO LO NECESARIO PARA EL DETALLE Y LA BOLETA
    cabecera = bd.consulta_uno(""" SELECT v.num_venta, v.fecha, v.forma_pago, v.total, v.estado, v.motivo_anulacion, v.fecha_anulacion,
            c.nombre, c.dni, COALESCE(u.nombre, '-'), COALESCE(ua.nombre, '-')
        FROM venta v
        INNER JOIN cliente c ON c.cod_cliente = v.cod_cliente
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
    num_venta = codigo_seleccionado(ui.tabla_ventas, filas["ventas"])
    venta = datos_venta(num_venta) if num_venta is not None else None
    ui.btn_boleta.setEnabled(venta is not None)
    ui.btn_anular.setEnabled(venta is not None and venta["estado"] == "REGISTRADA" and puede("anular"))
    if venta is None:
        ui.grupo_detalle_venta.setTitle("Detalle")
        ui.lbl_info_venta.setText("Selecciona una venta para ver su detalle.")
        ui.tabla_detalle_venta.setRowCount(0)
        ui.lbl_total_venta.setText("")
        return
    ui.grupo_detalle_venta.setTitle(f"Venta N° {venta['num']}")
    info = (f"<b>{escape(venta['cliente'])}</b> (DNI {venta['dni']})<br>{venta['fecha']:%d/%m/%Y}  ·  {venta['forma_pago']}"
            f"  ·  Atendió: {escape(venta['vendedor'])}")
    if venta["estado"] == "ANULADA":
        info += (f"<br><span style='color:{interfaz.COLOR_PELIGRO}'><b>ANULADA</b> el {venta['fecha_anulacion']:%d/%m/%Y %H:%M} "
                 f"por {escape(venta['anulada_por'])}. Motivo: {escape(venta['motivo'] or '')}</span>")
    ui.lbl_info_venta.setText(info)
    reconstruye_tabla(ui.tabla_detalle_venta, venta["lineas"],
                      lambda linea: [celda(linea[0]), celda(linea[1], True), celda(soles(linea[2]), True), celda(soles(linea[1] * linea[2]), True)])
    ui.lbl_total_venta.setText(f"Total: {soles(venta['total'])}")
def anula_venta():
    if not puede("anular"):
        aviso("Solo un administrador puede anular ventas.", "Sin permiso")
        return
    num_venta = codigo_seleccionado(ui.tabla_ventas, filas["ventas"])
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
    num_venta = num_venta or codigo_seleccionado(ui.tabla_ventas, filas["ventas"])
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
        Paragraph(f"<b>Cliente:</b> {escape(venta['cliente'])}  ·  <b>DNI:</b> {venta['dni']}", normal),
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
def abre_reportes():
    hoy = date.today()
    anios = [str(fila[0]) for fila in bd.consulta(""" SELECT YEAR(CURDATE()) UNION SELECT DISTINCT YEAR(fecha) FROM venta ORDER BY 1 DESC """)]
    seleccionado = ui.cmb_anio.currentText() or str(hoy.year)
    ui.cmb_anio.clear()
    ui.cmb_anio.addItems(anios)
    ui.cmb_anio.setCurrentText(seleccionado if seleccionado in anios else str(hoy.year))
    if not ultimo_reporte:
        ui.cmb_mes.setCurrentIndex(hoy.month - 1)
        muestra_reporte([], None)
    cambia_tipo_reporte()
def cambia_tipo_reporte():
    semanal = ui.cmb_tipo_reporte.currentText() == "Semanal"
    ui.lbl_semana.setVisible(semanal)
    ui.cmb_semana.setVisible(semanal)
def rango_semana(anio, mes, semana): # SEMANA 1: DIAS 1-7, 2: 8-14, 3: 15-21, 4: 22-28, 5: 29-FIN DE MES
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    inicio = (semana - 1) * 7 + 1
    if inicio > ultimo_dia:
        return None
    fin = ultimo_dia if semana == 5 else inicio + 6
    return date(anio, mes, inicio), date(anio, mes, fin)
def consulta_reporte(inicio, fin): # UNA FILA POR VENTA; LAS ANULADAS NO CUENTAN
    return bd.consulta(""" SELECT v.num_venta, v.fecha,
            GROUP_CONCAT(CONCAT(p.tipo, ' ', p.marca, ' x', d.cantidad) ORDER BY p.tipo SEPARATOR ', '),
            c.nombre, v.forma_pago, v.total
        FROM venta v
        INNER JOIN cliente c ON v.cod_cliente = c.cod_cliente
        INNER JOIN det_venta d ON d.num_venta = v.num_venta
        INNER JOIN producto p ON d.cod_producto = p.cod_producto
        WHERE v.fecha BETWEEN %s AND %s AND v.estado = 'REGISTRADA'
        GROUP BY v.num_venta, v.fecha, c.nombre, v.forma_pago, v.total
        ORDER BY v.fecha, v.num_venta """, (inicio, fin))
def genera_reporte():
    anio, mes = int(ui.cmb_anio.currentText()), ui.cmb_mes.currentIndex() + 1
    if ui.cmb_tipo_reporte.currentText() == "Semanal":
        semana = ui.cmb_semana.currentIndex() + 1
        rango = rango_semana(anio, mes, semana)
        if rango is None:
            aviso(f"{MESES[mes - 1]} de {anio} no tiene semana 5.")
            return
        titulo, archivo = f"Reporte semanal - {MESES[mes - 1]} {anio}, semana {semana}", f"reporte_semanal_{anio}-{mes:02d}_semana{semana}"
    else:
        rango = (date(anio, mes, 1), date(anio, mes, calendar.monthrange(anio, mes)[1]))
        titulo, archivo = f"Reporte mensual - {MESES[mes - 1]} {anio}", f"reporte_mensual_{anio}-{mes:02d}"
    datos = consulta_reporte(*rango)
    ultimo_reporte.clear()
    ultimo_reporte.update({"titulo": titulo, "archivo": archivo, "periodo": f"{rango[0]:%d/%m/%Y} al {rango[1]:%d/%m/%Y}",
                           "filas": datos, "total": sum((fila[5] for fila in datos), Decimal("0"))})
    muestra_reporte(datos, ultimo_reporte)
def muestra_reporte(datos, reporte):
    tabla = ui.tabla_reporte
    tabla.setRowCount(len(datos))
    for fila, (num_venta, fecha, productos, cliente, forma_pago, total) in enumerate(datos):
        for columna, item in enumerate([celda(num_venta, True), celda(f"{fecha:%d/%m/%Y}"), celda(productos), celda(cliente),
                                        celda(forma_pago), celda(soles(total), True)]):
            tabla.setItem(fila, columna, item)
    if reporte is None:
        ui.lbl_periodo.setText("Elige el periodo y pulsa «Generar reporte».")
        ui.lbl_resumen.setText("")
    else:
        ui.lbl_periodo.setText(f"{reporte['titulo']}  ·  del {reporte['periodo']}")
        ui.lbl_resumen.setText(f"{len(datos)} ventas  ·  Total: {soles(reporte['total'])}" if datos else "No hay ventas en este periodo.")
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
    datos = [["N° venta", "Fecha", "Productos", "Cliente", "Pago", "Total"]]
    for num_venta, fecha, productos, cliente, forma_pago, total in reporte["filas"]:
        datos.append([str(num_venta), f"{fecha:%d/%m/%Y}", Paragraph(escape(productos), texto_celda),
                      Paragraph(escape(cliente), texto_celda), forma_pago, soles(total)])
    datos.append(["", "", "", "", "TOTAL", soles(reporte["total"])])
    tabla = Table(datos, colWidths=[1.7*cm, 2.1*cm, 5.9*cm, 3.7*cm, 1.8*cm, 2.4*cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), turquesa),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#f2f4f6")]),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#c3c8cf")),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    contenido = [
        Paragraph(escape(reporte["titulo"]), estilos["Title"]),
        Paragraph(f"Periodo: del {reporte['periodo']}", estilos["Normal"]),
        Paragraph(f"{len(reporte['filas'])} ventas · Generado el {datetime.now():%d/%m/%Y %H:%M}", estilos["Normal"]),
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
    encabezados = ["N° venta", "Fecha", "Productos", "Cliente", "Pago", "Total"]
    relleno = PatternFill("solid", fgColor=interfaz.COLOR_PRIMARIO.lstrip("#"))
    for columna, texto in enumerate(encabezados, start=1):
        celda_excel = hoja.cell(row=5, column=columna, value=texto)
        celda_excel.font = Font(bold=True, color="FFFFFF")
        celda_excel.fill = relleno
        celda_excel.alignment = Alignment(horizontal="center")
    formato_soles = '"S/" #,##0.00'
    for fila, (num_venta, fecha, productos, cliente, forma_pago, total) in enumerate(reporte["filas"], start=6):
        for columna, valor in enumerate([num_venta, fecha, productos, cliente, forma_pago, total], start=1):
            hoja.cell(row=fila, column=columna, value=valor)
        hoja.cell(row=fila, column=2).number_format = "DD/MM/YYYY"
        hoja.cell(row=fila, column=6).number_format = formato_soles
    ultima = 5 + len(reporte["filas"])
    hoja.cell(row=ultima + 1, column=5, value="TOTAL").font = Font(bold=True)
    total = hoja.cell(row=ultima + 1, column=6, value=f"=SUM(F6:F{ultima})") # FORMULA: SE RECALCULA SI EDITAN EL ARCHIVO
    total.font = Font(bold=True)
    total.number_format = formato_soles
    for columna, ancho in zip("ABCDEF", (10, 12, 48, 28, 10, 14)):
        hoja.column_dimensions[columna].width = ancho
    hoja.freeze_panes = "A6"
    hoja.auto_filter.ref = f"A5:F{ultima}"
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
        return True
    except (bd.ErrorConfiguracion, pymysql.err.MySQLError) as error:
        logging.error("Sin conexión a la base de datos", exc_info=True)
        QMessageBox.critical(None, "Sin conexión", mensaje_error(error))
        return False
# INICIO
def configura_aplicacion(app):
    # LA INTERFAZ ESTA DISEÑADA PARA TEMA CLARO: SI EL SISTEMA USA MODO OSCURO, QT6 PONDRIA TEXTO CLARO SOBRE FONDOS CLAROS
    if hasattr(app.styleHints(), "setColorScheme"): # QT 6.8+
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    app.setStyle("Fusion") # SE VE IGUAL EN WINDOWS, LINUX Y MAC
    app.setStyleSheet(interfaz.ESTILO)
def crea_ventana():
    global ventana, ui
    ventana = QMainWindow()
    ui = interfaz.Interfaz(ventana)
    conecta_eventos()
    return ventana
def conecta_eventos(): # LAS SEÑALES SE CONECTAN UNA SOLA VEZ PARA NO REPETIR ACCIONES
    # MENU Y SESION
    ui.btn_inicio.clicked.connect(lambda: muestra_pagina(ui.btn_inicio, ui.inicio, abre_inicio))
    ui.btn_clientes.clicked.connect(lambda: muestra_pagina(ui.btn_clientes, ui.clientes, lambda: abre_entidad("cliente"), "clientes"))
    ui.btn_productos.clicked.connect(lambda: muestra_pagina(ui.btn_productos, ui.productos, lambda: abre_entidad("producto"), "productos"))
    ui.btn_venta.clicked.connect(lambda: muestra_pagina(ui.btn_venta, ui.venta, abre_venta, "venta"))
    ui.btn_ventas.clicked.connect(lambda: muestra_pagina(ui.btn_ventas, ui.ventas, busca_ventas, "ventas"))
    ui.btn_reportes.clicked.connect(lambda: muestra_pagina(ui.btn_reportes, ui.reportes, abre_reportes, "reportes"))
    ui.btn_usuarios.clicked.connect(lambda: muestra_pagina(ui.btn_usuarios, ui.usuarios, lambda: abre_entidad("usuario"), "usuarios"))
    ui.btn_cambiar_clave.clicked.connect(lambda: crea_dialogo_clave().exec())
    ui.btn_cerrar_sesion.clicked.connect(cierra_sesion)
    # CLIENTES, PRODUCTOS Y USUARIOS
    for entidad in ("cliente", "producto", "usuario"):
        p = pagina(entidad)
        p.buscador.textChanged.connect(lambda _texto, e=entidad: busca(e))
        p.tabla.itemSelectionChanged.connect(lambda e=entidad: selecciona(e))
        p.btn_nuevo.clicked.connect(lambda _marcado=False, e=entidad: nuevo(e))
        p.btn_guardar.clicked.connect(lambda _marcado=False, e=entidad: guardar(e))
        p.btn_eliminar.clicked.connect(lambda _marcado=False, e=entidad: eliminar(e))
        for campo in p.campos.values():
            if hasattr(campo, "returnPressed"): # ENTER EN EL FORMULARIO = GUARDAR
                campo.returnPressed.connect(lambda e=entidad: guardar(e))
    # VENTA
    ui.buscador_cliente_venta.textChanged.connect(busca_clientes_venta)
    ui.buscador_producto_venta.textChanged.connect(busca_productos_venta)
    ui.tabla_clientes_venta.itemSelectionChanged.connect(selecciona_cliente_venta)
    ui.tabla_productos_venta.itemSelectionChanged.connect(actualiza_disponible)
    ui.tabla_productos_venta.itemDoubleClicked.connect(agrega_producto) # DOBLE CLIC = AGREGAR
    ui.spn_cantidad.lineEdit().returnPressed.connect(agrega_producto) # ENTER EN CANTIDAD = AGREGAR
    ui.btn_agregar.clicked.connect(agrega_producto)
    ui.btn_quitar.clicked.connect(quita_producto)
    ui.btn_cancelar_venta.clicked.connect(cancela_venta)
    ui.btn_registrar_venta.clicked.connect(registra_venta)
    # HISTORIAL
    for filtro in (ui.fecha_desde.dateChanged, ui.fecha_hasta.dateChanged, ui.cmb_estado_venta.currentIndexChanged, ui.buscador_ventas.textChanged):
        filtro.connect(busca_ventas)
    ui.tabla_ventas.itemSelectionChanged.connect(muestra_detalle_venta)
    ui.btn_boleta.clicked.connect(lambda: guarda_boleta())
    ui.btn_anular.clicked.connect(anula_venta)
    # REPORTES
    ui.cmb_tipo_reporte.currentIndexChanged.connect(cambia_tipo_reporte)
    ui.btn_generar_reporte.clicked.connect(genera_reporte)
    ui.btn_exportar_pdf.clicked.connect(lambda: exporta(".pdf"))
    ui.btn_exportar_excel.clicked.connect(lambda: exporta(".xlsx"))
ventana = ui = None
if __name__ == "__main__":
    logging.basicConfig(handlers=[logging.FileHandler(ARCHIVO_LOG, encoding="utf-8", delay=True)], # EL ARCHIVO SE CREA SOLO SI HAY ERRORES
                        level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    configura_aplicacion(app)
    sys.excepthook = maneja_error_inesperado
    if not verifica_conexion():
        sys.exit(1)
    if not pide_login(): # CANCELAR EL INGRESO NO ES UN ERROR
        sys.exit(0)
    crea_ventana()
    aplica_sesion()
    ventana.show()
    sys.exit(app.exec())
