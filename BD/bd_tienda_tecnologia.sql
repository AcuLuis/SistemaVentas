use bd_tienda_tecnologia;
CREATE TABLE cliente (
    cod_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255),
    dni VARCHAR(15),
    telefono VARCHAR(15),
    sexo VARCHAR(9)
);

CREATE TABLE producto (
    cod_producto INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(255),
    marca VARCHAR(255),
    precio float,
    cantidad INT
);

CREATE TABLE det_venta (
    num_venta int,
    fecha DATE,
    tipo VARCHAR(25),
    cod_cliente INT,
    cod_producto INT,
    FOREIGN KEY (cod_cliente) REFERENCES cliente(cod_cliente),
    FOREIGN KEY (cod_producto) REFERENCES producto(cod_producto)
);