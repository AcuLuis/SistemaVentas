# Sistema de Ventas e Inventario

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-interfaz-41CD52?logo=qt&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?logo=mysql&logoColor=white)
![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green)
[![Estrellas](https://img.shields.io/github/stars/AcuLuis/SistemaVentas?style=social)](https://github.com/AcuLuis/SistemaVentas/stargazers)

Aplicación de escritorio para gestionar las ventas de una tienda de tecnología: clientes, productos con control de stock, ventas con boleta en PDF, historial con anulaciones y reportes exportables a PDF y Excel. Está hecha en Python con **PyQt6** y usa **MySQL** como base de datos.

![Panel de inicio](docs/img/inicio.png)

## Características

- **Inicio de sesión con roles.** Administrador y Vendedor, con contraseñas cifradas (PBKDF2) y bloqueo temporal tras varios intentos fallidos.
- **Panel de inicio.** Ventas del día y del mes, clientes registrados, productos con stock bajo y los más vendidos.
- **Clientes y productos.** Tabla con buscador y formulario en la misma pantalla. Valida DNI (8 dígitos), teléfono (9 dígitos), precios y DNI repetidos.
- **Ventas.**
  - El stock se valida al agregar y otra vez al registrar.
  - Precio, subtotal y total en soles, y forma de pago (contado o crédito).
  - Todo se guarda en una sola transacción: si algo falla, no se registra nada.
- **Boleta en PDF.** Se ofrece al registrar cada venta y se puede volver a generar desde el historial.
- **Historial de ventas.** Filtros por fecha, estado y cliente. El administrador puede anular una venta indicando el motivo, y el stock se devuelve automáticamente.
- **Reportes mensuales y semanales.** Se exportan a **PDF** o **Excel** (con fechas y montos como valores reales y el total con fórmula).
- **Usuarios.** El administrador crea cuentas, asigna roles y activa o desactiva el acceso.

## Capturas

| Inicio de sesión | Nueva venta |
|:---:|:---:|
| ![Inicio de sesión](docs/img/login.png) | ![Nueva venta](docs/img/venta.png) |

| Historial de ventas (con una venta anulada) | Reportes |
|:---:|:---:|
| ![Historial de ventas](docs/img/historial.png) | ![Reportes](docs/img/reportes.png) |

| Clientes | Productos |
|:---:|:---:|
| ![Clientes](docs/img/clientes.png) | ![Productos](docs/img/productos.png) |

| Usuarios | Boleta en PDF |
|:---:|:---:|
| ![Usuarios](docs/img/usuarios.png) | ![Boleta en PDF](docs/img/boleta.png) |

Reporte exportado a PDF:

![Reporte en PDF](docs/img/reporte_pdf.png)

## Requisitos

- Python 3.12 (es la versión con la que se probó)
- MySQL 8.0.16 o superior (probado con 8.4)
- Las dependencias de [requirements.txt](requirements.txt): PyQt6, PyMySQL, reportlab, openpyxl y cryptography

## Instalación

1. **Clona el repositorio**

   ```bash
   git clone https://github.com/AcuLuis/SistemaVentas.git
   cd SistemaVentas
   ```

2. **Crea un entorno virtual e instala las dependencias**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # Linux / macOS
   pip install -r requirements.txt
   ```

3. **Crea la base de datos.** El primer script crea la base y sus tablas. El segundo carga datos de ejemplo y los usuarios iniciales.

   ```bash
   mysql -u root -p --default-character-set=utf8mb4 -e "source BD/bd_tienda_tecnologia.sql"
   mysql -u root -p --default-character-set=utf8mb4 -e "source BD/datos_bd.sql"
   ```

4. **(Recomendado) Crea un usuario de MySQL solo para la aplicación**

   ```sql
   CREATE USER 'tienda'@'localhost' IDENTIFIED BY 'una_contraseña_segura';
   GRANT ALL ON bd_tienda_tecnologia.* TO 'tienda'@'localhost';
   ```

5. **Configura la conexión.** Copia [config.ejemplo.ini](config.ejemplo.ini) como `config.ini` y completa tus datos. El archivo `config.ini` está en `.gitignore`, así que tus credenciales no se suben al repositorio.

   ```ini
   [mysql]
   host = 127.0.0.1
   port = 3306
   user = tienda
   password = una_contraseña_segura
   database = bd_tienda_tecnologia
   ```

6. **Ejecuta la aplicación**

   ```bash
   python control.py
   ```

## Usuarios de ejemplo

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `vendedor` | `vendedor123` | Vendedor |

> [!IMPORTANT]
> Cambia estas contraseñas apenas instales el sistema. Puedes hacerlo desde **Cambiar contraseña**, en la parte inferior del menú.

Qué puede hacer cada rol:

| Opción | Administrador | Vendedor |
|---|:---:|:---:|
| Inicio, Clientes, Nueva venta, Historial y boletas | ✅ | ✅ |
| Eliminar clientes | ✅ | — |
| Productos, Reportes y Usuarios | ✅ | — |
| Anular ventas | ✅ | — |

## Actualizar una base de datos anterior

Si creaste la base con una versión anterior de este proyecto, haz un respaldo y ejecuta la migración **una sola vez**. Convierte las ventas al nuevo formato y crea el usuario `admin` / `admin123`.

```bash
mysqldump -u root -p bd_tienda_tecnologia > respaldo.sql
mysql -u root -p --default-character-set=utf8mb4 -e "source BD/actualizar_bd.sql"
```

## Crear un ejecutable (.exe)

```bash
pip install pyinstaller
pyinstaller SistemaVentas.spec
```

El ejecutable queda en `dist/SistemaVentas.exe`. Para distribuirlo, coloca un `config.ini` en la misma carpeta que el `.exe`.

## Estructura del proyecto

```text
SistemaVentas/
├── control.py             # Punto de entrada: lógica de pantallas, ventas, reportes y sesión
├── interfaz.py            # Ventanas y pantallas construidas con PyQt6
├── bd.py                  # Configuración, conexión y consultas parametrizadas a MySQL
├── seguridad.py           # Cifrado y verificación de contraseñas
├── BD/
│   ├── bd_tienda_tecnologia.sql   # Esquema de la base de datos
│   ├── datos_bd.sql               # Datos de ejemplo y usuarios iniciales
│   └── actualizar_bd.sql          # Migración desde la versión anterior
├── iconos/                # Íconos de la interfaz
├── docs/img/              # Capturas usadas en este README
├── config.ejemplo.ini     # Plantilla de config.ini
├── SistemaVentas.spec     # Configuración para crear el .exe
└── requirements.txt
```

## Seguridad

- Todas las consultas SQL son parametrizadas, lo que evita la inyección SQL.
- Las contraseñas de los usuarios se guardan cifradas con PBKDF2-SHA256 y sal aleatoria.
- Las credenciales de MySQL viven en `config.ini`, fuera del código y del repositorio.
- Los errores inesperados se muestran con un mensaje claro y se registran en `sistema_ventas.log`.

## Solución de problemas

- **"No se pudo conectar con MySQL":** verifica que el servidor esté encendido y que los datos de `config.ini` sean correctos.
- **Tildes o símbolos raros al consultar desde la consola de Windows:** los datos están bien; es la consola la que no muestra UTF-8. Ejecuta `chcp 65001` y usa `mysql --default-character-set=utf8mb4`.
- **Otros errores:** revisa `sistema_ventas.log`, junto a `control.py` o al `.exe`. Ese archivo solo se crea si ocurrió algún error.

## Contribuciones

¡Las contribuciones son bienvenidas! Para proponer un cambio:

1. Haz un fork del repositorio.
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Haz tus cambios y un commit: `git commit -m "Añade nueva funcionalidad"`
4. Sube la rama: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request.

## ⭐ ¿Te gustó el proyecto?

Si este sistema te resultó útil, te sirvió para aprender o simplemente te gustó, **me harías muy feliz regalándole una estrella** ⭐ al repositorio. Es un gesto pequeño que me anima a seguir mejorándolo y a compartir más proyectos.

[![Dale una estrella en GitHub](https://img.shields.io/badge/⭐_Dale_una_estrella-en_GitHub-yellow?style=for-the-badge&logo=github)](https://github.com/AcuLuis/SistemaVentas)

¡Gracias por pasar por aquí! 🙌

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Si tienes alguna pregunta o sugerencia, escríbeme a luisacudev@gmail.com.
