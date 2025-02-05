
use bd_tienda_tecnologia;

INSERT INTO cliente (nombre, dni, telefono, sexo) VALUES 
('Juan Pérez', '12345678', '987654321', 'Masculino'),
('María García', '87654321', '912345678', 'Femenino'),
('Luis Torres', '11223344', '934567890', 'Masculino'),
('Ana López', '44332211', '956789012', 'Femenino'),
('Carlos Díaz', '55667788', '978901234', 'Masculino');

INSERT INTO producto (tipo, marca, precio, cantidad) VALUES 
('Laptop', 'HP', 2500.00, 10),
('Smartphone', 'Samsung', 1200.00, 15),
('Tablet', 'Apple', 1800.00, 8),
('Monitor', 'LG', 750.00, 12),
('Teclado', 'Logitech', 150.00, 20);

INSERT INTO det_venta (num_venta, fecha, tipo, cod_cliente, cod_producto) VALUES 
(1, '2024-02-01', 'Contado', 1, 1),  -- Juan Pérez compró una Laptop HP
(2, '2024-02-03', 'Crédito', 2, 2),  -- María García compró un Smartphone Samsung
(3, '2024-02-05', 'Contado', 3, 3),  -- Luis Torres compró una Tablet Apple
(4, '2024-02-07', 'Crédito', 4, 4),  -- Ana López compró un Monitor LG
(5, '2024-02-09', 'Contado', 5, 5);  -- Carlos Díaz compró un Teclado Logitech

