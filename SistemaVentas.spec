# -*- mode: python ; coding: utf-8 -*-
# GENERA EL EJECUTABLE dist/SistemaVentas.exe CON:  pyinstaller SistemaVentas.spec
# AL DISTRIBUIRLO, COLOCA config.ini (COPIA DE config.ejemplo.ini) EN LA MISMA CARPETA QUE EL .exe

a = Analysis(
    ["control.py"],
    datas=[("iconos", "iconos"), ("inicio_logo.jpg", ".")],
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="SistemaVentas",
    console=False, # APLICACION DE VENTANAS: SIN CONSOLA NEGRA
    upx=False,
)
