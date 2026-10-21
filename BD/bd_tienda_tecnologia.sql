SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS bd_tienda_tecnologia CHARACTER SET utf8mb4;
use bd_tienda_tecnologia;
CREATE TABLE cliente (
    cod_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    dni CHAR(8) NOT NULL UNIQUE,
    telefono VARCHAR(9) NOT NULL,
    sexo VARCHAR(9) NOT NULL
);

CREATE TABLE producto (
    cod_producto INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(255) NOT NULL,
    marca VARCHAR(255) NOT NULL,
    precio DECIMAL(10,2) NOT NULL CHECK (precio >= 0),
    cantidad INT NOT NULL DEFAULT 0 CHECK (cantidad >= 0)
);

-- USUARIOS DEL SISTEMA: LA CLAVE SE GUARDA CIFRADA (PBKDF2), NUNCA EN TEXTO PLANO
CREATE TABLE usuario (
    cod_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    clave VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('ADMIN', 'VENDEDOR')),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- CABECERA: UNA FILA POR VENTA
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

-- DETALLE: UNA FILA POR PRODUCTO VENDIDO, CON EL PRECIO DEL MOMENTO DE LA VENTA
CREATE TABLE det_venta (
    num_venta INT NOT NULL,
    cod_producto INT NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (num_venta, cod_producto),
    FOREIGN KEY (num_venta) REFERENCES venta(num_venta),
    FOREIGN KEY (cod_producto) REFERENCES producto(cod_producto)
);
