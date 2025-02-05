import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox,QTableWidgetItem,QFileDialog
from PyQt5.QtGui import QPixmap
import sistema_venta as sistema_venta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import pymysql
import os
def conexion():
    conec = pymysql.connect(host="127.0.0.1", user = "localhost", password= "123456789",
                            database = "bd_tienda_tecnologia")
    return conec
# BUSQUEDA SEGUN BD
def busca_cliente():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM cliente WHERE cod_cliente LIKE '%{ui.txt_busca_bd_cliente.text()}%' OR nombre LIKE '%{ui.txt_busca_bd_cliente.text()}%' OR dni = '{ui.txt_busca_bd_cliente.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_cliente.setRowCount(len(datos))
        ui.tabla_cliente.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_cliente.setItem(fila, columna, celda)
    else:
        ui.tabla_cliente.setRowCount(0)
    cursor.close()  
    con.close()
def busca_producto():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM producto WHERE cod_producto LIKE '%{ui.txt_busca_bd_producto.text()}%' OR tipo LIKE '%{ui.txt_busca_bd_producto.text()}%' OR marca = '{ui.txt_busca_bd_producto.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_producto.setRowCount(len(datos))
        ui.tabla_producto.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_producto.setItem(fila, columna, celda)
    else:
        ui.tabla_producto.setRowCount(0)  
    cursor.close()
    con.close()
# LLENA TABLA DE LA BD PRINCIPAL Y AL INICIO
def llena_bd_principal(valida):
    fila = 0
    columna = 0
    con = conexion()
    cursor = con.cursor()
    datos = ""
    if valida == "cliente": # DATOS CLIENTE
        ui.tabla_producto.setRowCount(0)
        ui.tabla_cliente.setRowCount(0)
        cursor.execute(" SELECT * FROM cliente ")
        datos = cursor.fetchall()
        ui.tabla_cliente.setRowCount(len(datos))
        ui.tabla_cliente.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_cliente.setItem(fila, columna, celda)
    if valida == "producto": # DATOS PRODUCTO
        ui.tabla_cliente.setRowCount(0)
        ui.tabla_producto.setRowCount(0)
        cursor.execute(" SELECT * FROM producto ")
        datos = cursor.fetchall()
        ui.tabla_producto.setRowCount(len(datos))
        ui.tabla_producto.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_producto.setItem(fila, columna, celda)
    cursor.close()
    con.close()
def error_seleciona(): # ERROR SI NO SELECCIONAS
    mensaje = QMessageBox()
    mensaje.setIcon(QMessageBox.Critical)
    mensaje.setText("DEBE SELECIONAR UNA OPCION...")
    mensaje.setWindowTitle("Error")
    mensaje.exec_()
def cliente(): # ACCION AL SELECCIONAR CLIENTE
    indice = ui.contenedor_paginas.indexOf(ui.bd_cliente)
    ui.contenedor_paginas.setCurrentIndex(indice)
    llena_bd_principal("cliente")
    ui.txt_busca_bd_cliente.textChanged.connect(busca_cliente)
def producto(): # ACCION AL SELECCIONAR PRODUCTO
    indice = ui.contenedor_paginas.indexOf(ui.bd_producto)
    ui.contenedor_paginas.setCurrentIndex(indice)
    llena_bd_principal("producto")
    ui.txt_busca_bd_producto.textChanged.connect(busca_producto)
def decide_bd(): # SELECCIONA BD SEGUN OPCION
    if ui.rbtn_cliente.isChecked(): # CLIENTE
        indice = ui.contenedor_paginas.indexOf(ui.bd_cliente)
        llena_bd_principal("cliente")
    elif ui.rbtn_producto.isChecked(): # PRODUCTO
        indice = ui.contenedor_paginas.indexOf(ui.bd_producto)
        llena_bd_principal("producto")
    else:
        indice = ui.contenedor_paginas.indexOf(ui.vacio) # VACIO
        error_seleciona()
    ui.contenedor_paginas.setCurrentIndex(indice)
# REGISTRO
def verifica_registrar():
    if ui.rbtn_cliente.isChecked():
        if ui.txt_nombre_cliente.text()=="" or ui.txt_dni_cliente.text()=="" or ui.txt_telefono_cliente.text()=="" or ui.cmb_sexo_cliente.currentIndex()==0:
            QMessageBox.critical(None, 'Error', 'EXISTEN DATOS FALTANTES')
            return False
        else:
            return True
    elif ui.rbtn_producto.isChecked():
        if ui.txt_tipo_producto.text()=="" or ui.txt_marca_producto.text() =="" or ui.txt_precio_producto.text()=="" or ui.txt_cantidad_producto.text()=="":
            QMessageBox.critical(None, 'Error', 'EXISTEN DATOS FALTANTES')
            return False
        else:
            return True    
def id_siguiente_registro():
    con = conexion()
    cursor = con.cursor()
    if ui.rbtn_cliente.isChecked():
        cursor.execute("SELECT MAX(cod_cliente) + 1 as sigue FROM cliente;")
    elif ui.rbtn_producto.isChecked():
        cursor.execute("SELECT MAX(cod_producto) + 1 as sigue FROM producto;")
    resultado = cursor.fetchone()
    if resultado:
        siguiente_id = resultado[0]
        cursor.close()
        return str(siguiente_id) 
def limpia_registro():
    if ui.rbtn_cliente.isChecked():
        ui.txt_cod_cliente.setText(id_siguiente_registro())
        ui.txt_nombre_cliente.setText("")
        ui.txt_dni_cliente.setText("")
        ui.txt_telefono_cliente.setText("")
        ui.cmb_sexo_cliente.setCurrentIndex(0)
    if ui.rbtn_producto.isChecked():
        ui.txt_cod_producto.setText(id_siguiente_registro())
        ui.txt_tipo_producto.setText("")
        ui.txt_marca_producto.setText("")
        ui.txt_precio_producto.setText("")
        ui.txt_cantidad_producto.setText("") 
def registro():
    if ui.rbtn_cliente.isChecked():
        con = conexion()
        cursor = con.cursor()
        try:
            sql = "INSERT INTO cliente VALUES (%s, %s, %s, %s, %s)"
            valores = (int(ui.txt_cod_cliente.text()), ui.txt_nombre_cliente.text(), ui.txt_dni_cliente.text(), ui.txt_telefono_cliente.text(), ui.cmb_sexo_cliente.currentText())
            cursor.execute(sql, valores)
            con.commit()
            QMessageBox.information(None, 'Éxito', 'Registro exitoso')
        except Exception as e:
            QMessageBox.critical(None, 'Error', f'Error al registrar: {str(e)}')
        cursor.close()
        con.close()
    elif ui.rbtn_producto.isChecked():
        con = conexion()
        cursor = con.cursor()
        try:
            sql = "INSERT INTO producto VALUES (%s, %s, %s, %s, %s)"
            valores = (int(ui.txt_cod_producto.text()), ui.txt_tipo_producto.text(), ui.txt_marca_producto.text(), float(ui.txt_precio_producto.text()), int(ui.txt_cantidad_producto.text()))
            cursor.execute(sql, valores)
            con.commit()
            QMessageBox.information(None, 'Éxito', 'Registro exitoso')
        except Exception as e:
            QMessageBox.critical(None, 'Error', f'Error al registrar: {str(e)}')
        cursor.close()
        con.close()
    confirmacion = QMessageBox.question(None, 'Confirmación', '¿Deseas limpiar los datos después del registro?', QMessageBox.Yes | QMessageBox.No)
    if confirmacion == QMessageBox.Yes:
        limpia_registro()
def decide_registrar(): # SELECCIONA REGISTRO SEGUN OPCION
    if ui.rbtn_cliente.isChecked(): # CLIENTE
        indice = ui.contenedor_paginas.indexOf(ui.registra_cliente)
        ui.txt_cod_cliente.setText(id_siguiente_registro())
        ui.btn_limpiar_cliente.clicked.connect(limpia_registro)
        ui.btn_registrar_cliente.clicked.connect(registro)
    elif ui.rbtn_producto.isChecked(): # PRODUCTO
        indice = ui.contenedor_paginas.indexOf(ui.registra_producto)
        ui.txt_cod_producto.setText(id_siguiente_registro())
        ui.btn_limpiar_producto.clicked.connect(limpia_registro)
        ui.btn_registar_producto.clicked.connect(registro)
    else:
        indice = ui.contenedor_paginas.indexOf(ui.vacio) # VACIO
        error_seleciona()
    ui.contenedor_paginas.setCurrentIndex(indice)
# BUSCAR SEGUN BD ACTUALIZAR
def busca_cliente_actualizar():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM cliente WHERE cod_cliente LIKE '%{ui.txt_busca_actualiza_cliente.text()}%' OR nombre LIKE '%{ui.txt_busca_actualiza_cliente.text()}%' OR dni = '{ui.txt_busca_actualiza_cliente.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_actualiza_cliente.setRowCount(len(datos))
        ui.tabla_actualiza_cliente.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_actualiza_cliente.setItem(fila, columna, celda)
    else:
        ui.tabla_actualiza_cliente.setRowCount(0)
    cursor.close() 
    con.close() 
def busca_producto_actualizar():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM producto WHERE cod_producto LIKE '%{ui.txt_busca_actualiza_producto.text()}%' OR tipo LIKE '%{ui.txt_busca_actualiza_producto.text()}%' OR marca = '{ui.txt_busca_actualiza_producto.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_actualiza_producto.setRowCount(len(datos))
        ui.tabla_actualiza_producto.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_actualiza_producto.setItem(fila, columna, celda)
    else:
        ui.tabla_actualiza_producto.setRowCount(0) 
    cursor.close()
    con.close() 
# ACTUALIZAR
def limpiar_actualizar():
    if ui.rbtn_cliente.isChecked():
        ui.txt_actualiza_cod_cliente.setText("")
        ui.txt_actualiza_nombre_cliente.setText("")
        ui.txt_actualiza_dni.setText("")
        ui.txt_actualiza_telefono.setText("")
        ui.cmb_actualiza_sexo.setCurrentIndex(0)
    if ui.rbtn_producto.isChecked():
        ui.txt_actualiza_cod_producto.setText("")
        ui.txt_actualiza_tipo_producto.setText("")
        ui.txt_actualiza_marca_producto.setText("")
        ui.txt_actualiza_precio_producto.setText("")
        ui.txt_actualiza_cantidad_producto.setText("")
def verifica_actualizacion():
    if ui.rbtn_cliente.isChecked():
        if ui.txt_actualiza_cod_cliente.text()=="" or ui.txt_actualiza_nombre_cliente.text()=="" or ui.txt_actualiza_dni.text()=="" or ui.txt_actualiza_telefono.text()=="" or ui.cmb_actualiza_sexo.currentIndex()==0:
            QMessageBox.critical(None, 'Error', 'EXISTEN DATOS FALTANTES')
            return False
        else:
            return True
    elif ui.rbtn_producto.isChecked():
        if ui.txt_actualiza_cod_producto.text()=="" or ui.txt_actualiza_tipo_producto.text()=="" or ui.txt_actualiza_marca_producto.text()=="" or ui.txt_actualiza_precio_producto.text()=="" or ui.txt_actualiza_cantidad_producto.text()=="":
            QMessageBox.critical(None, 'Error', 'EXISTEN DATOS FALTANTES')
            return False
        else:
            return True
def indice_cambiado_actualiza():
    if ui.rbtn_cliente.isChecked():
        tab_clie = ui.tabla_actualiza_cliente
        idx = tab_clie.currentRow()
        if idx >= 0 and idx < tab_clie.rowCount():
            item = tab_clie.item(idx, 0)
            if item is not None:
                ui.txt_actualiza_cod_cliente.setText(item.text())
                ui.txt_actualiza_nombre_cliente.setText(tab_clie.item(idx, 1).text())
                ui.txt_actualiza_dni.setText(tab_clie.item(idx, 2).text())
                ui.txt_actualiza_telefono.setText(tab_clie.item(idx, 3).text())
                if tab_clie.item(idx, 4).text() == "MASCULINO":
                    ui.cmb_actualiza_sexo.setCurrentIndex(1)
                elif tab_clie.item(idx, 4).text()== "FEMENINO":
                    ui.cmb_actualiza_sexo.setCurrentIndex(2)
    elif ui.rbtn_producto.isChecked():
        tab_produ = ui.tabla_actualiza_producto
        idx = tab_produ.currentRow()
        if idx >= 0 and idx < tab_produ.rowCount():
            item = tab_produ.item(idx, 0)
            if item is not None:
                ui.txt_actualiza_cod_producto.setText(item.text())
                ui.txt_actualiza_tipo_producto.setText(tab_produ.item(idx, 1).text())
                ui.txt_actualiza_marca_producto.setText(tab_produ.item(idx, 2).text())
                ui.txt_actualiza_precio_producto.setText(tab_produ.item(idx, 3).text())
                ui.txt_actualiza_cantidad_producto.setText(tab_produ.item(idx,4).text())
def llena_tabla_actualizar():
    fila = 0
    columna = 0
    con = conexion()
    cursor = con.cursor()
    datos = ""
    if ui.rbtn_cliente.isChecked(): # CLIENTE
        ui.tabla_actualiza_cliente.setRowCount(0)
        cursor.execute("SELECT * FROM cliente ")
        datos = cursor.fetchall()
        ui.tabla_actualiza_cliente.setRowCount(len(datos))
        ui.tabla_actualiza_cliente.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_actualiza_cliente.setItem(fila, columna, celda)
        ui.tabla_actualiza_cliente.itemSelectionChanged.connect(indice_cambiado_actualiza)
        cursor.close()
        con.close()
    elif ui.rbtn_producto.isChecked(): # PRODUCTO
        ui.tabla_actualiza_producto.setRowCount(0)
        cursor.execute("SELECT * FROM producto")
        datos = cursor.fetchall()
        ui.tabla_actualiza_producto.setRowCount(len(datos))
        ui.tabla_actualiza_producto.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_actualiza_producto.setItem(fila, columna, celda)
        ui.tabla_actualiza_producto.itemSelectionChanged.connect(indice_cambiado_actualiza)
        cursor.close()
        con.close()
def actualizacion():
    if ui.rbtn_cliente.isChecked():
        if verifica_actualizacion() == True:
            try:
                con = conexion()
                cursor = con.cursor()
                codigo = ui.txt_actualiza_cod_cliente.text()
                nuevo_nombre = ui.txt_actualiza_nombre_cliente.text()
                nuevo_dni = ui.txt_actualiza_dni.text()
                nuevo_telefono = ui.txt_actualiza_telefono.text()
                if ui.cmb_actualiza_sexo.currentIndex() == 1:
                    nuevo_sexo = "MASCULINO"
                else:
                    nuevo_sexo = "FEMENINO"
                sql = f"UPDATE cliente SET nombre = '{nuevo_nombre}', dni = '{nuevo_dni}', telefono = '{nuevo_telefono}', sexo = '{nuevo_sexo}' WHERE cod_cliente = {int(codigo)};"
                cursor.execute(sql)
                con.commit()
                cursor.close()
                con.close()
                QMessageBox.information(None, 'Éxito', 'Los datos se actualizaron correctamente.')
                llena_tabla_actualizar()
                limpiar_actualizar()
                # Añadir la confirmación antes de limpiar los datos
                confirmacion = QMessageBox.question(None, 'Confirmación', '¿Deseas limpiar los datos después de la actualización?', QMessageBox.Yes | QMessageBox.No)
                if confirmacion == QMessageBox.Yes:
                    limpiar_actualizar()
                # Si no hay confirmación, los datos permanecerán en el formulario para su revisión adicional
            except Exception as e:
                QMessageBox.critical(None, 'Error', f'Error al actualizar datos: {str(e)}')
    elif ui.rbtn_producto.isChecked():
        if verifica_actualizacion() == True:
            try:
                con = conexion()
                cursor = con.cursor()
                codigo = ui.txt_actualiza_cod_producto.text()
                nuevo_tipo = ui.txt_actualiza_tipo_producto.text()
                nuevo_marca = ui.txt_actualiza_marca_producto.text()
                nuevo_precio = ui.txt_actualiza_precio_producto.text()
                nuevo_cantidad = ui.txt_actualiza_cantidad_producto.text()
                sql = f"UPDATE producto SET tipo = '{nuevo_tipo}', marca = '{nuevo_marca}', precio = {float(nuevo_precio)}, cantidad = {int(nuevo_cantidad)}  WHERE cod_producto = {int(codigo)};"
                cursor.execute(sql)
                con.commit()
                cursor.close()
                con.close()
                QMessageBox.information(None, 'Éxito', 'Los datos se actualizaron correctamente.')
                llena_tabla_actualizar()
                limpiar_actualizar()
                # Añadir la confirmación antes de limpiar los datos
                confirmacion = QMessageBox.question(None, 'Confirmación', '¿Deseas limpiar los datos después de la actualización?', QMessageBox.Yes | QMessageBox.No)
                if confirmacion == QMessageBox.Yes:
                    limpiar_actualizar()
                # Si no hay confirmación, los datos permanecerán en el formulario para su revisión adicional
            except Exception as e:
                QMessageBox.critical(None, 'Error', f'Error al actualizar datos: {str(e)}')
def decide_actualizar(): # SELECCIONA ACTUALIZAR SEGUN OPCION
    if ui.rbtn_cliente.isChecked(): # CLIENTE
        indice = ui.contenedor_paginas.indexOf(ui.actualiza_cliente)
        llena_tabla_actualizar()
        ui.btn_actualizar_cliente.clicked.connect(actualizacion)
        ui.btn_actualizar_cliente_limpia.clicked.connect(limpiar_actualizar)
        ui.txt_busca_actualiza_cliente.textChanged.connect(busca_cliente_actualizar)
    elif ui.rbtn_producto.isChecked(): # PRODUCTO
        indice = ui.contenedor_paginas.indexOf(ui.actualiza_producto)
        llena_tabla_actualizar()
        ui.btn_actualizar_producto.clicked.connect(actualizacion)
        ui.btn_actualizar_producto_limpia.clicked.connect(limpiar_actualizar)
        ui.txt_busca_actualiza_producto.textChanged.connect(busca_producto_actualizar)
    else:
        indice = ui.contenedor_paginas.indexOf(ui.vacio) # VACIO
        error_seleciona()
    ui.contenedor_paginas.setCurrentIndex(indice)
# BUSCA SEGUN BD ELIMINAR
def busca_cliente_eliminar():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM cliente WHERE cod_cliente LIKE '%{ui.txt_busca_elimina_cliente.text()}%' OR nombre LIKE '%{ui.txt_busca_elimina_cliente.text()}%' OR dni = '{ui.txt_busca_elimina_cliente.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_elimina_cliente.setRowCount(len(datos))
        ui.tabla_elimina_cliente.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_elimina_cliente.setItem(fila, columna, celda)
    else:
        ui.tabla_elimina_cliente.setRowCount(0)
    cursor.close() 
    con.close() 
def busca_producto_eliminar():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM producto WHERE cod_producto LIKE '%{ui.txt_busca_elimina_producto.text()}%' OR tipo LIKE '%{ui.txt_busca_elimina_producto.text()}%' OR marca = '{ui.txt_busca_elimina_producto.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_elimina_producto.setRowCount(len(datos))
        ui.tabla_elimina_producto.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_elimina_producto.setItem(fila, columna, celda)
    else:
        ui.tabla_elimina_producto.setRowCount(0)
    cursor.close()  
    con.close()
# ELIMINAR
def limpiar_eliminar():
    if ui.rbtn_cliente.isChecked():
        ui.txt_elimina_cod_cliente.setText("")
        ui.txt_elimina_nombre_cliente.setText("")
        ui.txt_elimina_dni.setText("")
        ui.txt_elimina_telefono.setText("")
        ui.cmb_elimina_sexo.setCurrentIndex(0)
    elif ui.rbtn_producto.isChecked():
        ui.txt_elimina_cod_producto.setText("")
        ui.txt_elimina_tipo_producto.setText("")
        ui.txt_elimina_marca_producto.setText("")
        ui.txt_elimina_precio_producto.setText("")
        ui.txt_elimina_cantidad_producto.setText("")
def verifica_eliminar():
    if ui.rbtn_cliente.isChecked():
        if ui.txt_elimina_nombre_cliente.text() == "" or ui.txt_elimina_dni.text()=="" or ui.txt_elimina_telefono.text()=="" or ui.cmb_elimina_sexo.currentIndex()==0:
            QMessageBox.critical(None, 'Error', 'EXISTEN DATOS FALTANTES')
            return False
        else:
            return True
    elif ui.rbtn_producto.isChecked():
        if ui.txt_elimina_tipo_producto.text()=="" or ui.txt_elimina_marca_producto.text()=="" or ui.txt_elimina_precio_producto.text()=="" or ui.txt_elimina_cantidad_producto.text()=="":
            QMessageBox.critical(None, 'Error', 'EXISTEN DATOS FALTANTES')
            return False
        else:
            return True 
def indice_cambiado_elimina():
    if ui.rbtn_cliente.isChecked():
        tab_clie = ui.tabla_elimina_cliente
        idx = tab_clie.currentRow()
        if idx >= 0 and idx < tab_clie.rowCount():
            item = tab_clie.item(idx, 0)
            if item is not None:
                ui.txt_elimina_cod_cliente.setText(item.text())
                ui.txt_elimina_nombre_cliente.setText(tab_clie.item(idx, 1).text())
                ui.txt_elimina_dni.setText(tab_clie.item(idx, 2).text())
                ui.txt_elimina_telefono.setText(tab_clie.item(idx, 3).text())
                if tab_clie.item(idx, 4).text() == "MASCULINO":
                    ui.cmb_elimina_sexo.setCurrentIndex(1)
                elif tab_clie.item(idx, 4).text()== "FEMENINO":
                    ui.cmb_elimina_sexo.setCurrentIndex(2)
    elif ui.rbtn_producto.isChecked():
        tab_produ = ui.tabla_elimina_producto
        idx = tab_produ.currentRow()
        if idx >= 0 and idx < tab_produ.rowCount():
            item = tab_produ.item(idx, 0)
            if item is not None:
                ui.txt_elimina_cod_producto.setText(item.text())
                ui.txt_elimina_tipo_producto.setText(tab_produ.item(idx, 1).text())
                ui.txt_elimina_marca_producto.setText(tab_produ.item(idx, 2).text())
                ui.txt_elimina_precio_producto.setText(tab_produ.item(idx, 3).text())
                ui.txt_elimina_cantidad_producto.setText(tab_produ.item(idx,4).text())
def llena_tabla_eliminar():
    fila = 0
    columna = 0
    con = conexion()
    cursor = con.cursor()
    datos = ""
    if ui.rbtn_cliente.isChecked(): # CLIENTE
        ui.tabla_elimina_cliente.setRowCount(0)
        cursor.execute("SELECT * FROM cliente ")
        datos = cursor.fetchall()
        ui.tabla_elimina_cliente.setRowCount(len(datos))
        ui.tabla_elimina_cliente.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_elimina_cliente.setItem(fila, columna, celda)
        ui.tabla_elimina_cliente.itemSelectionChanged.connect(indice_cambiado_elimina)
        cursor.close()
        con.close()
    elif ui.rbtn_producto.isChecked(): # PRODUCTO
        ui.tabla_elimina_producto.setRowCount(0)
        cursor.execute("SELECT * FROM producto")
        datos = cursor.fetchall()
        ui.tabla_elimina_producto.setRowCount(len(datos))
        ui.tabla_elimina_producto.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_elimina_producto.setItem(fila, columna, celda)
        ui.tabla_elimina_producto.itemSelectionChanged.connect(indice_cambiado_elimina)
        cursor.close() 
        con.close()  
def eliminacion():
    if ui.rbtn_cliente.isChecked():
        if verifica_eliminar():
            try:
                con = conexion()
                cursor = con.cursor()
                codigo = int(ui.txt_elimina_cod_cliente.text())
                sql = f"DELETE FROM cliente WHERE cod_cliente = {codigo};"
                cursor.execute(sql)
                con.commit()
                cursor.close()
                con.close()
                QMessageBox.information(None, 'Éxito', 'Los datos se eliminaron correctamente.')
                llena_tabla_eliminar()
                limpiar_eliminar()
                # Añadir la confirmación antes de limpiar los datos
                confirmacion = QMessageBox.question(None, 'Confirmación', '¿Deseas limpiar los datos después de la eliminación?', QMessageBox.Yes | QMessageBox.No)
                if confirmacion == QMessageBox.Yes:
                    limpiar_eliminar()
                # Si no hay confirmación, los datos permanecerán en el formulario para su revisión adicional
            except Exception as e:
                QMessageBox.critical(None, 'Error', f'Error al eliminar datos: {str(e)}')
    elif ui.rbtn_producto.isChecked():
        if verifica_eliminar():
            try:
                con = conexion()
                cursor = con.cursor()
                codigo = int(ui.txt_elimina_cod_producto.text())
                sql = f"DELETE FROM producto WHERE cod_producto = {codigo};"
                cursor.execute(sql)
                con.commit()
                cursor.close()
                con.close()
                QMessageBox.information(None, 'Éxito', 'Los datos se eliminaron correctamente.')
                llena_tabla_eliminar()
                limpiar_eliminar()
                # Añadir la confirmación antes de limpiar los datos
                confirmacion = QMessageBox.question(None, 'Confirmación', '¿Deseas limpiar los datos después de la eliminación?', QMessageBox.Yes | QMessageBox.No)
                if confirmacion == QMessageBox.Yes:
                    limpiar_eliminar()
                # Si no hay confirmación, los datos permanecerán en el formulario para su revisión adicional
            except Exception as e:
                QMessageBox.critical(None, 'Error', f'Error al eliminar datos: {str(e)}')
def decide_eliminar(): # SELECCIONA ACTUALIZAR SEGUN OPCION
    if ui.rbtn_cliente.isChecked(): # CLIENTE
        indice = ui.contenedor_paginas.indexOf(ui.elimina_cliente)
        llena_tabla_eliminar()
        ui.btn_elimina_cliente.clicked.connect(eliminacion)
        ui.btn_elimina_cliente_limpia.clicked.connect(limpiar_eliminar)
        ui.txt_busca_elimina_cliente.textChanged.connect(busca_cliente_eliminar)
    elif ui.rbtn_producto.isChecked(): # PRODUCTO
        indice = ui.contenedor_paginas.indexOf(ui.elimina_producto)
        llena_tabla_eliminar()
        ui.btn_elimina_producto.clicked.connect(eliminacion)
        ui.btn_elimina_producto_limpia.clicked.connect(limpiar_eliminar)
        ui.txt_busca_elimina_producto.textChanged.connect(busca_producto_eliminar)
    else:
        indice = ui.contenedor_paginas.indexOf(ui.vacio) # VACIO
        error_seleciona()
    ui.contenedor_paginas.setCurrentIndex(indice)
# BUSCA VENTA SEGUN BD
def busca_cliente_venta():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM cliente WHERE cod_cliente LIKE '%{ui.txt_busca_venta_cliente.text()}%' OR nombre LIKE '%{ui.txt_busca_venta_cliente.text()}%' OR dni = '{ui.txt_busca_venta_cliente.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_cliente_venta.setRowCount(len(datos))
        ui.tabla_cliente_venta.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_cliente_venta.setItem(fila, columna, celda)
    else:
        ui.tabla_cliente_venta.setRowCount(0)
    cursor.close()
    con.close()  
def busca_producto_venta():
    con = conexion()
    cursor = con.cursor()
    consulta = f""" SELECT * FROM producto WHERE cod_producto LIKE '%{ui.txt_busca_venta_producto.text()}%' OR tipo LIKE '%{ui.txt_busca_venta_producto.text()}%' OR marca = '{ui.txt_busca_venta_producto.text()}'; """
    cursor.execute(consulta)
    datos = cursor.fetchall()
    if datos:  # Verifica si hay datos antes de procesarlos
        ui.tabla_producto_venta.setRowCount(len(datos))
        ui.tabla_producto_venta.setColumnCount(len(datos[0]))
        for fila, fila_datos in enumerate(datos):
            for columna, valor in enumerate(fila_datos):
                celda = QTableWidgetItem(str(valor))
                ui.tabla_producto_venta.setItem(fila, columna, celda)
    else:
        ui.tabla_producto_venta.setRowCount(0)  
    cursor.close()
    con.close()
# VENTA
def verifica_datos_lista_venta():
    if ui.cod_cliente_venta.text()=="" or ui.nombre_cliente_venta.text() == "" or ui.cod_producto_venta.text()=="" or ui.tipo_producto_venta.text()=="" or ui.cantida_producto_venta.text()=="":
        return False
    else:
        return True
def id_siguiente_venta():
    con = conexion()
    cursor = con.cursor()
    cursor.execute("SELECT MAX(num_venta) + 1 as sigue FROM det_venta;")
    resultado = cursor.fetchone()
    if resultado:
        siguiente_id = resultado[0]
        cursor.close()
        return str(siguiente_id) 
    con.close()
def fecha_siguiente():
    con = conexion()
    cursor = con.cursor()
    cursor.execute("SELECT CURDATE();")
    resultado = cursor.fetchone()
    if resultado:
        siguiente_fecha = resultado[0]
        cursor.close()
        return str(siguiente_fecha) 
    con.close()
def limpia_datos_agrego():
        ui.cod_producto_venta.setText("")
        ui.tipo_producto_venta.setText("")
        ui.cantida_producto_venta.setText("")
def agregar_lista_venta():
    if verifica_datos_lista_venta():
        cod_cliente = ui.cod_cliente_venta.text()
        cod_producto = ui.cod_producto_venta.text()
        tipo = ui.tipo_producto_venta.text()
        cantidad = ui.cantida_producto_venta.text()
        row_count = ui.tabla_lista_venta.rowCount()
        ui.tabla_lista_venta.setRowCount(row_count + 1)
        ui.tabla_lista_venta.setItem(row_count, 0, QTableWidgetItem(tipo))
        ui.tabla_lista_venta.setItem(row_count, 1, QTableWidgetItem(cod_producto))
        ui.tabla_lista_venta.setItem(row_count, 2, QTableWidgetItem(cod_cliente))
        ui.tabla_lista_venta.setItem(row_count, 3, QTableWidgetItem(cantidad))
    else:
        QMessageBox.critical(None, 'Error', 'EXISTEN DATOS FALTANTES')
def limpiar_datos_venta():
        ui.cod_cliente_venta.setText("")
        ui.nombre_cliente_venta.setText("")
        ui.cod_producto_venta.setText("")
        ui.tipo_producto_venta.setText("")
        ui.cantida_producto_venta.setText("")
def limpiar_tabla_venta():
        if ui.tabla_lista_venta.rowCount() > 0:
            ui.tabla_lista_venta.setRowCount(0)
            QMessageBox.information(None,'Éxito', 'Se limpiaron los datos de la tabla.')
def limpiar_tabla_venta_cambia_cliente():
    if ui.tabla_lista_venta.rowCount() > 0:
        ui.tabla_lista_venta.setRowCount(0)
def indice_cambia_venta(val):
    if val =="cliente":
        limpiar_datos_venta()
        limpiar_tabla_venta_cambia_cliente()
        tab_clie = ui.tabla_cliente_venta
        idx = tab_clie.currentRow()
        if idx >= 0 and idx < tab_clie.rowCount():
            item = tab_clie.item(idx, 0)
            if item is not None:
                ui.cod_cliente_venta.setText(item.text())
                ui.nombre_cliente_venta.setText(tab_clie.item(idx, 1).text())
    elif val == "producto":
        tab_clie = ui.tabla_producto_venta
        idx = tab_clie.currentRow()
        if idx >= 0 and idx < tab_clie.rowCount():
            item = tab_clie.item(idx, 0)
            if item is not None:
                ui.cod_producto_venta.setText(item.text())
                ui.tipo_producto_venta.setText(tab_clie.item(idx, 1).text())
def refresca_data():
    try:
        con = conexion()
        cursor = con.cursor()
        # Realiza una consulta SQL para obtener los datos del informe
        query = """ SELECT num_venta, fecha, tipo, cod_cliente, cod_producto, cantidad FROM det_venta
            WHERE num_venta = %s  # Filtra por el número de venta que acabas de registrar """
        num_venta = int(ui.num_venta.text())  # Obtén el número de venta registrado
        cursor.execute(query, (num_venta,))
        data = cursor.fetchall()
        # Actualiza la tabla de informe con los nuevos datos
        ui.tabla_reporte_semanal.setRowCount(len(data))
        ui.tabla_reporte_semanal.setColumnCount(4)  # Asegúrate de que haya suficientes columnas
        for row, row_data in enumerate(data):
            for col, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                ui.tabla_reporte_semanal.setItem(row, col, item)
        con.commit()
        cursor.close()
        con.close()
    except Exception as e:
        print(f"Error al actualizar datos del informe: {str(e)}")
def registra_venta():
    if ui.tabla_lista_venta.rowCount() > 0:
        try:
            con = conexion()
            cursor = con.cursor()
            num_venta = id_siguiente_venta()
            fecha = fecha_siguiente()
            for row in range(ui.tabla_lista_venta.rowCount()):
                tipo = ui.tabla_lista_venta.item(row, 0).text()
                cod_producto = ui.tabla_lista_venta.item(row, 1).text()
                cod_cliente = ui.tabla_lista_venta.item(row, 2).text()
                cantidad = ui.tabla_lista_venta.item(row, 3).text()
                sql = "INSERT INTO det_venta (num_venta, fecha, tipo, cod_cliente, cod_producto, cantidad) VALUES (%s, %s, %s, %s, %s, %s)"
                valores = (int(num_venta), fecha, tipo, int(cod_cliente), int(cod_producto), int(cantidad))
                cursor.execute(sql, valores)
            con.commit()
            cursor.close()
            con.close()
            QMessageBox.information(None, 'Éxito', 'SE REGISTRARON LOS DATOS')
            refresca_data()
            # Confirmar si se debe limpiar la tabla
            confirmacion = QMessageBox.question(None, 'Confirmación', '¿Deseas limpiar la tabla?', QMessageBox.Yes | QMessageBox.No)
            if confirmacion == QMessageBox.Yes:
                limpiar_tabla_venta_cambia_cliente()
                limpiar_datos_venta()
        except Exception as e:
            QMessageBox.warning(None, 'Aviso', f"Error al insertar en la tabla SQL: {str(e)}")
def llena_tabla_venta_general():
    fila = 0
    columna = 0
    con = conexion()
    cursor = con.cursor()
    datos = ""
    ui.tabla_cliente_venta.setRowCount(0)
    cursor.execute("SELECT * FROM cliente ;")
    datos = cursor.fetchall()
    ui.tabla_cliente_venta.setRowCount(len(datos))
    ui.tabla_cliente_venta.setColumnCount(len(datos[0]))
    for fila, fila_datos in enumerate(datos):
        for columna, valor in enumerate(fila_datos):
            celda = QTableWidgetItem(str(valor))
            ui.tabla_cliente_venta.setItem(fila, columna, celda)
    ui.tabla_cliente_venta.itemSelectionChanged.connect(lambda:indice_cambia_venta("cliente"))
    cursor.close()
    fila_p = 0
    columna_p = 0
    cursor_p = con.cursor()
    datos_p = ""
    ui.tabla_producto_venta.setRowCount(0)
    cursor_p.execute("SELECT * FROM producto ;")
    datos_p = cursor_p.fetchall()
    ui.tabla_producto_venta.setRowCount(len(datos_p))
    ui.tabla_producto_venta.setColumnCount(len(datos_p[0]))
    for fila_p, fila_datos in enumerate(datos_p):
        for columna_p, valor in enumerate(fila_datos):
            celda = QTableWidgetItem(str(valor))
            ui.tabla_producto_venta.setItem(fila_p, columna_p, celda)
    ui.tabla_producto_venta.itemSelectionChanged.connect(lambda:indice_cambia_venta("producto"))
    cursor_p.close()
    con.close()
def venta(): # PAGINA DE VENTA
    indice = ui.contenedor_paginas.indexOf(ui.venta_general)
    ui.contenedor_paginas.setCurrentIndex(indice)
    llena_tabla_venta_general()
    num_venta_sigue = id_siguiente_venta()
    ui.num_venta.setText(num_venta_sigue)
    fecha_venta_sigue = fecha_siguiente()
    ui.fecha_venta.setText(fecha_venta_sigue)
    ui.btn_venta_limpia_datos.clicked.connect(limpiar_datos_venta)
    ui.btn_venta_limpia_tabla.clicked.connect(limpiar_tabla_venta)
    ui.btn_agregar_lista_venta.clicked.connect(agregar_lista_venta)
    ui.btn_registrar_venta.clicked.connect(registra_venta)
    ui.txt_busca_venta_cliente.textChanged.connect(busca_cliente_venta)
    ui.txt_busca_venta_producto.textChanged.connect(busca_producto_venta)
# PDF REPORTE SEMANAL
def pdf_semanal():
    # Desactivar el botón de exportación mientras se genera el PDF
    ui.btn_pdf_semanal.setEnabled(False)
    # Obtener la ruta de la carpeta "Descargas" del sistema
    download_folder = QFileDialog.getExistingDirectory(None, "Selecciona la carpeta de Descargas")
    if download_folder:
        file_name = "reporte_semanal.pdf"
        file_path = os.path.join(download_folder, file_name)
        # Obtén datos de la tabla
        data = []
        title_row = ["Reporte Semanal"]
        data.append(title_row)
        # Agrega el encabezado en el orden deseado
        header = ["nro_venta", "fecha", "tipo producto", "cliente"]
        data.append(header)
        for row in range(ui.tabla_reporte_semanal.rowCount()):
            row_data = []
            for col in range(ui.tabla_reporte_semanal.columnCount()):
                item = ui.tabla_reporte_semanal.item(row, col)
                row_data.append(item.text())
            data.append(row_data)
        # Comprobar si el archivo ya existe y manejar el número de versión
        version = 1
        while os.path.exists(file_path):
            version += 1
            file_name = f"reporte_semanal({version}).pdf"
            file_path = os.path.join(download_folder, file_name)
        # Crear el PDF con un título
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        pdf_table = Table(data)
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), (0.9, 0.9, 0.9)),
            ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), (0.85, 0.85, 0.85)),
            ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
        ]))
        doc.build([pdf_table])
        # Habilitar nuevamente el botón de exportación
        ui.btn_pdf_semanal.setEnabled(True)
        # Notificar al usuario sobre la ubicación del archivo generado
        QMessageBox.information(None, 'Información', f'Reporte generado y guardado en: {file_path}')
# REPORTE SEMANAL
def limpiar_cmb_reporte_semanal():
    ui.cmb_reporte_semanal_anio.setCurrentIndex(0)
    ui.cmb_meses_reporte_semanal.setCurrentIndex(0)
    ui.cmb_semanas_reporte_semanal.setCurrentIndex(0)
def verifica_fechas_semanal():
    if (ui.cmb_reporte_semanal_anio.currentIndex()==0
        or ui.cmb_meses_reporte_semanal.currentIndex()==0
        or ui.cmb_semanas_reporte_semanal.currentIndex()==0):
        return False
    else:
        return True
def obtener_min_max_fecha(semana):
    min = 0
    max = 0
    if semana == 1:
        min = 0
        max =8
    elif semana == 2:
        min = 7
        max =16
    elif semana == 3:
        min = 15
        max =24
    elif semana == 4:
        min = 23
        max =32
    lista=[]
    lista.append(min)
    lista.append(max)
    return lista
def generar_reporte_semanal():
    if verifica_fechas_semanal()== True:
        indice = ui.contenedor_paginas.indexOf(ui.reporte_semanal)
        ui.contenedor_paginas.setCurrentIndex(indice)
        try:
            con = conexion()
            cursor = con.cursor()
            lista = obtener_min_max_fecha(ui.cmb_semanas_reporte_semanal.currentIndex())
            mini, maxi = lista[0], lista[1]
            query = f""" SELECT det_venta.num_venta, det_venta.fecha, producto.tipo, cliente.nombre
                FROM det_venta
                INNER JOIN producto ON det_venta.cod_producto = producto.cod_producto
                INNER JOIN cliente ON det_venta.cod_cliente = cliente.cod_cliente
                WHERE YEAR(det_venta.fecha) = {int(ui.cmb_reporte_semanal_anio.currentText())}
                AND MONTH(det_venta.fecha) = {ui.cmb_meses_reporte_semanal.currentIndex()}
                AND DAY(det_venta.fecha) BETWEEN {mini} AND {maxi}; """
            cursor.execute(query)
            data = cursor.fetchall()
            ui.tabla_reporte_semanal.setRowCount(len(data))
            ui.tabla_reporte_semanal.setColumnCount(4)
            for row, row_data in enumerate(data):
                for col, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    ui.tabla_reporte_semanal.setItem(row, col, item)
            cursor.close()
            con.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {str(e)}")
    else:
        QMessageBox.warning(None, 'Aviso', 'FALTAN ELEGIR FECHAS')
def volver_semanal():
    indice = ui.contenedor_paginas.indexOf(ui.ingresa_fecha_semanal)
    ui.contenedor_paginas.setCurrentIndex(indice)
def reporte_venta_semanal(): # PAGINA DE REPORTE SEMANAL
    indice = ui.contenedor_paginas.indexOf(ui.ingresa_fecha_semanal)
    ui.contenedor_paginas.setCurrentIndex(indice)
    ui.btn_calcular_semanal.clicked.connect(generar_reporte_semanal)
    ui.btn_reporte_semanal_limpiar.clicked.connect(limpiar_cmb_reporte_semanal)
    ui.btn_volver_semanal.clicked.connect(volver_semanal)
    ui.btn_pdf_semanal.clicked.connect(pdf_semanal)
# PDF REPORTE MENSUAL
def pdf_mensual():
    # Desactivar el botón de exportación mientras se genera el PDF
    ui.btn_pdf_mensual.setEnabled(False)
    # Obtener la ruta de la carpeta "Descargas" del sistema
    download_folder = QFileDialog.getExistingDirectory(None, "Selecciona la carpeta de Descargas")
    if download_folder:
        file_name = "reporte_mensual.pdf"
        file_path = os.path.join(download_folder, file_name)
        # Obtén datos de la tabla
        data = []
        title_row = ["Reporte Mensual"]
        data.append(title_row)
        # Agrega el encabezado en el orden deseado
        header = ["nro_venta", "fecha", "tipo producto", "cliente"]
        data.append(header)
        for row in range(ui.tabla_reporte_mensual.rowCount()):
            row_data = []
            for col in range(ui.tabla_reporte_mensual.columnCount()):
                item = ui.tabla_reporte_mensual.item(row, col)
                row_data.append(item.text())
            data.append(row_data)
        # Comprobar si el archivo ya existe y manejar el número de versión
        version = 1
        while os.path.exists(file_path):
            version += 1
            file_name = f"reporte_mensual({version}).pdf"
            file_path = os.path.join(download_folder, file_name)
        # Crear el PDF con un título
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        pdf_table = Table(data)
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), (0.9, 0.9, 0.9)),
            ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), (0.85, 0.85, 0.85)),
            ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
        ]))
        doc.build([pdf_table])
        # Habilitar nuevamente el botón de exportación
        ui.btn_pdf_mensual.setEnabled(True)
        # Notificar al usuario sobre la ubicación del archivo generado
        QMessageBox.information(None, 'Información', f'Reporte generado y guardado en: {file_path}')
# REPORTE MENSUAL
def verifica_fechas_mensual():
    if ui.cmb_reporte_mensual_anio.currentIndex()==0 or ui.cmb_meses_reporte_mensual.currentIndex()==0:
        return False
    else:
        return True
def generar_reporte_mensual():
    if verifica_fechas_mensual()==True:
        indice = ui.contenedor_paginas.indexOf(ui.reporte_mensual)
        ui.contenedor_paginas.setCurrentIndex(indice)
        try:
            con = conexion()
            cursor = con.cursor()
            query = f""" SELECT det_venta.num_venta, det_venta.fecha, producto.tipo, cliente.nombre
                FROM det_venta
                INNER JOIN producto ON det_venta.cod_producto = producto.cod_producto
                INNER JOIN cliente ON det_venta.cod_cliente = cliente.cod_cliente
                WHERE YEAR(det_venta.fecha) = {ui.cmb_reporte_mensual_anio.currentText()}
                AND MONTH(det_venta.fecha) = {ui.cmb_meses_reporte_mensual.currentIndex()} """
            cursor.execute(query)
            data = cursor.fetchall()
            ui.tabla_reporte_mensual.setRowCount(len(data))
            ui.tabla_reporte_mensual.setColumnCount(4)
            for row, row_data in enumerate(data):
                for col, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    ui.tabla_reporte_mensual.setItem(row, col, item)

            cursor.close()
            con.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {str(e)}")
    else:
        QMessageBox.warning(None, 'Aviso', 'FALTAN ELEGIR FECHAS')
def limpia_cmb_mensual():
    ui.cmb_reporte_mensual_anio.setCurrentIndex(0)
    ui.cmb_meses_reporte_mensual.setCurrentIndex(0)
def volver_mensual():
    indice = ui.contenedor_paginas.indexOf(ui.ingresa_fecha_mensual)
    ui.contenedor_paginas.setCurrentIndex(indice)
def reporte_venta_mensual(): # PAGINA DE REPORTE MENSUAL
    indice = ui.contenedor_paginas.indexOf(ui.ingresa_fecha_mensual)
    ui.contenedor_paginas.setCurrentIndex(indice)
    ui.btn_reporte_mensual_limpiar.clicked.connect(limpia_cmb_mensual)
    ui.btn_calcula_reporte_mensual.clicked.connect(generar_reporte_mensual)
    ui.btn_volver_mensual.clicked.connect(volver_mensual)
    ui.btn_pdf_mensual.clicked.connect(pdf_mensual)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana_sistema_venta = QMainWindow()
    ui = sistema_venta.Ui_MainWindow()
    ui.setupUi(ventana_sistema_venta)
    indice = ui.contenedor_paginas.indexOf(ui.vacio)
    ui.contenedor_paginas.setCurrentIndex(indice)
    pixmap = QPixmap("inicio_logo.jpg")
    ui.label_50.setGeometry(150, 100, 800, 400)
    ui.label_50.setPixmap(pixmap)
    ui.rbtn_cliente.clicked.connect(cliente)
    ui.rbtn_producto.clicked.connect(producto)
    ui.btn_base_datos.clicked.connect(decide_bd)
    ui.btn_registrar.clicked.connect(decide_registrar)
    ui.btn_actualizar.clicked.connect(decide_actualizar)
    ui.btn_eliminar.clicked.connect(decide_eliminar)
    ui.btn_venta.clicked.connect(venta)
    ui.btn_reporte_semanal.clicked.connect(reporte_venta_semanal)
    ui.btn_reporte_mensual.clicked.connect(reporte_venta_mensual)
    ventana_sistema_venta.show()
    sys.exit(app.exec_())