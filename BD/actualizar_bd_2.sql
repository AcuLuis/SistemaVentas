-- Ejecutar UNA sola vez si tu base ya tiene la tabla usuario (version con inicio de sesion).
-- 1. Permite registrar ventas a "Cliente varios", sin cliente registrado.
-- 2. Permite pedir el cambio de una contraseña temporal al ingresar.
SET NAMES utf8mb4;
use bd_tienda_tecnologia;

ALTER TABLE venta MODIFY cod_cliente INT NULL;
ALTER TABLE usuario ADD COLUMN debe_cambiar_clave BOOLEAN NOT NULL DEFAULT FALSE;
