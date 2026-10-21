
SET NAMES utf8mb4;
use bd_tienda_tecnologia;

INSERT INTO cliente (nombre, dni, telefono, sexo) VALUES
('Juan Pérez', '12345678', '987654321', 'MASCULINO'),
('María García', '87654321', '912345678', 'FEMENINO'),
('Luis Torres', '11223344', '934567890', 'MASCULINO'),
('Ana López', '44332211', '956789012', 'FEMENINO'),
('Carlos Díaz', '55667788', '978901234', 'MASCULINO');

INSERT INTO producto (tipo, marca, precio, cantidad) VALUES
('Laptop', 'HP', 2500.00, 10),
('Smartphone', 'Samsung', 1200.00, 15),
('Tablet', 'Apple', 1800.00, 8),
('Monitor', 'LG', 750.00, 12),
('Teclado', 'Logitech', 150.00, 20);

-- USUARIOS DE EJEMPLO (CAMBIA SUS CONTRASEÑAS AL INSTALAR):
-- admin / admin123 (Administrador)   vendedor / vendedor123 (Vendedor)
INSERT INTO usuario (usuario, nombre, clave, rol) VALUES
('admin', 'Administrador', 'pbkdf2_sha256$200000$578f65022f5a71c3091307b9c7dc09f8$716ada68247917e58faea5d1e2dd80c47d439279703d4bbdd2c5111cad6991f0', 'ADMIN'),
('vendedor', 'Vendedor de tienda', 'pbkdf2_sha256$200000$d6d63cce1d6a40a90d6d997b70097b9a$ed9077111a21004685e717b6b06bcd4e85d712dc82ad6cf1067aa5f7a7b10e0b', 'VENDEDOR');

INSERT INTO venta (num_venta, fecha, forma_pago, cod_cliente, total, cod_usuario) VALUES
(1, '2024-02-01', 'Contado', 1, 2500.00, 2),  -- Juan Pérez compró una Laptop HP
(2, '2024-02-03', 'Crédito', 2, 1200.00, 2),  -- María García compró un Smartphone Samsung
(3, '2024-02-05', 'Contado', 3, 1800.00, 2),  -- Luis Torres compró una Tablet Apple
(4, '2024-02-07', 'Crédito', 4, 750.00, 1),   -- Ana López compró un Monitor LG
(5, '2024-02-09', 'Contado', 5, 300.00, 2);   -- Carlos Díaz compró dos Teclados Logitech

INSERT INTO det_venta (num_venta, cod_producto, cantidad, precio_unitario) VALUES
(1, 1, 1, 2500.00),
(2, 2, 1, 1200.00),
(3, 3, 1, 1800.00),
(4, 4, 1, 750.00),
(5, 5, 2, 150.00);

