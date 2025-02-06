# Sistema de Ventas y Gestión de Inventario

Este proyecto es un sistema de ventas y gestión de inventario desarrollado en Python utilizando la biblioteca `PyQt5` para la interfaz gráfica y `pymysql` para la conexión y gestión de una base de datos MySQL. El sistema permite gestionar clientes, productos, ventas y generar reportes semanales y mensuales en formato PDF.

## Características Principales

- **Gestión de Clientes**: Permite registrar, actualizar, eliminar y buscar clientes en la base de datos.
- **Gestión de Productos**: Permite registrar, actualizar, eliminar y buscar productos en la base de datos.
- **Ventas**: Permite registrar ventas, asociando clientes y productos, y gestionar la cantidad de productos vendidos.
- **Reportes**: Genera reportes semanales y mensuales de ventas en formato PDF.
- **Interfaz Gráfica Intuitiva**: La interfaz de usuario es fácil de usar, con menús y paneles de configuración accesibles.

## Requisitos

- Python 3.x
- PyQt5
- pymysql
- reportlab (para la generación de PDFs)

## Instalación

1. Clona este repositorio o descarga el código fuente.
2. Asegúrate de tener Python 3.x instalado en tu sistema.
3. Instala las dependencias necesarias:

   ```bash
   pip install PyQt5 pymysql reportlab

4. Configura la base de datos MySQL:
- Crea una base de datos llamada bd_tienda_tecnologia.
- Importa el archivo SQL proporcionado en el repositorio para crear las tablas necesarias.
5. Ejecuta la aplicación.

## Uso
- **Gestión de Clientes**:
Selecciona la opción "Cliente" en el menú principal.
Puedes registrar nuevos clientes, actualizar información existente, eliminar clientes o buscar clientes en la base de datos.

- **Gestión de Productos**:
Selecciona la opción "Producto" en el menú principal.
Puedes registrar nuevos productos, actualizar información existente, eliminar productos o buscar productos en la base de datos.

- **Ventas**:
Selecciona la opción "Venta" en el menú principal.
Asocia un cliente y un producto, ingresa la cantidad vendida y registra la venta.
Puedes limpiar los datos de la venta o la tabla de ventas si es necesario.

- **Reportes**:
Selecciona la opción "Reporte Semanal" o "Reporte Mensual" en el menú principal.
Ingresa las fechas correspondientes y genera el reporte.
El reporte se guardará en formato PDF en la carpeta de descargas.

## Estructura del Código

- **Conexión a la Base de Datos**: La función conexion() maneja la conexión a la base de datos MySQL.

- **Gestión de Clientes y Productos**: Las funciones busca_cliente(), busca_producto(), registro(), actualizacion(), y eliminacion() gestionan las operaciones CRUD para clientes y productos.

- **Ventas**: Las funciones agregar_lista_venta(), registra_venta(), y refresca_data() gestionan el proceso de ventas.

- **Reportes**: Las funciones generar_reporte_semanal(), generar_reporte_mensual(), pdf_semanal(), y pdf_mensual() generan y exportan reportes en formato PDF.

## Contribuciones
Las contribuciones son bienvenidas. Si deseas contribuir, por favor sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama (git checkout -b feature/nueva-funcionalidad).
3. Realiza tus cambios y haz commit (git commit -am 'Añade nueva funcionalidad').
4. Haz push a la rama (git push origin feature/nueva-funcionalidad).
5. Abre un Pull Request.

## Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## Contacto
Si tienes alguna pregunta o sugerencia, no dudes en contactarme en luisacudev@gmail.com.
