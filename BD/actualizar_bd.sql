-- Ejecutar UNA sola vez si la base de datos se creó con la versión anterior del esquema
-- (det_venta con fecha, tipo y cod_cliente en cada fila). Haz un respaldo antes.
SET NAMES utf8mb4;
use bd_tienda_tecnologia;

-- det_venta antigua: agrega cantidad si no existe
SET @tiene_cantidad = (SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'bd_tienda_tecnologia' AND TABLE_NAME = 'det_venta' AND COLUMN_NAME = 'cantidad');
SET @sql = IF(@tiene_cantidad = 0, 'ALTER TABLE det_venta ADD COLUMN cantidad INT NOT NULL DEFAULT 1', 'DO 0');
PREPARE paso FROM @sql;
EXECUTE paso;
DEALLOCATE PREPARE paso;

UPDATE cliente SET sexo = UPPER(sexo);

ALTER TABLE producto
    MODIFY precio DECIMAL(10,2) NOT NULL,
    MODIFY cantidad INT NOT NULL DEFAULT 0;

-- USUARIOS: SE CREA UN ADMINISTRADOR INICIAL (admin / admin123). CAMBIA SU CONTRASEÑA AL INGRESAR
CREATE TABLE usuario (
    cod_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    clave VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('ADMIN', 'VENDEDOR')),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);
INSERT INTO usuario (usuario, nombre, clave, rol) VALUES
('admin', 'Administrador', 'pbkdf2_sha256$200000$578f65022f5a71c3091307b9c7dc09f8$716ada68247917e58faea5d1e2dd80c47d439279703d4bbdd2c5111cad6991f0', 'ADMIN');

-- CABECERA DE VENTA
CREATE TABLE venta (
    num_venta INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    forma_pago VARCHAR(10) NOT NULL,
    cod_cliente INT NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    cod_usuario INT NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'REGISTRADA' CHECK (estado IN ('REGISTRADA', 'ANULADA')),
    fecha_anulacion DATETIME NULL,
    motivo_anulacion VARCHAR(255) NULL,
    cod_usuario_anula INT NULL,
    FOREIGN KEY (cod_cliente) REFERENCES cliente(cod_cliente),
    FOREIGN KEY (cod_usuario) REFERENCES usuario(cod_usuario),
    FOREIGN KEY (cod_usuario_anula) REFERENCES usuario(cod_usuario)
);

INSERT INTO venta (num_venta, fecha, forma_pago, cod_cliente, total)
SELECT num_venta,
       COALESCE(MIN(fecha), CURDATE()),
       IF(MIN(tipo) IN ('Contado', 'Crédito'), MIN(tipo), 'Contado'),
       MIN(cod_cliente),
       0
FROM det_venta
WHERE num_venta IS NOT NULL AND cod_cliente IS NOT NULL
GROUP BY num_venta;

-- DETALLE NUEVO (el precio histórico no existía: se toma el precio actual del producto)
CREATE TABLE det_venta_nueva (
    num_venta INT NOT NULL,
    cod_producto INT NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (num_venta, cod_producto),
    FOREIGN KEY (num_venta) REFERENCES venta(num_venta),
    FOREIGN KEY (cod_producto) REFERENCES producto(cod_producto)
);

INSERT INTO det_venta_nueva (num_venta, cod_producto, cantidad, precio_unitario)
SELECT d.num_venta, d.cod_producto, SUM(d.cantidad), p.precio
FROM det_venta d
INNER JOIN venta v ON v.num_venta = d.num_venta
INNER JOIN producto p ON p.cod_producto = d.cod_producto
GROUP BY d.num_venta, d.cod_producto, p.precio;

UPDATE venta v SET total = (
    SELECT COALESCE(SUM(d.cantidad * d.precio_unitario), 0)
    FROM det_venta_nueva d WHERE d.num_venta = v.num_venta);

DROP TABLE det_venta;
RENAME TABLE det_venta_nueva TO det_venta;

-- Último paso: falla si hay DNIs repetidos; corrígelos y vuelve a ejecutar solo esta línea
ALTER TABLE cliente ADD UNIQUE (dni);
