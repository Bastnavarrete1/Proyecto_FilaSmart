CREATE DATABASE IF NOT EXISTS filasmart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE filasmart;

CREATE TABLE IF NOT EXISTS usuarios (
  id_usuario BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  correo VARCHAR(255) NOT NULL UNIQUE,
  `contraseña` VARCHAR(255) NOT NULL COMMENT 'Hash de contraseña, nunca texto plano',
  rol ENUM('cliente','admin','funcionario') NOT NULL DEFAULT 'cliente',
  fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sucursales (
  id_sucursal BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  direccion VARCHAR(255) NOT NULL,
  comuna VARCHAR(120) NOT NULL,
  telefono VARCHAR(30),
  estado ENUM('activa','inactiva') NOT NULL DEFAULT 'activa'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS servicios (
  id_servicio BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_sucursal BIGINT UNSIGNED NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  descripcion TEXT,
  duracion_estimada SMALLINT UNSIGNED NOT NULL DEFAULT 10 COMMENT 'Minutos por atención',
  estado ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  UNIQUE KEY uq_servicio_sucursal (id_sucursal,nombre),
  CONSTRAINT fk_servicios_sucursal FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS filas (
  id_fila BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_servicio BIGINT UNSIGNED NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  estado ENUM('activa','inactiva') NOT NULL DEFAULT 'activa',
  fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_fila_servicio (id_servicio,nombre),
  CONSTRAINT fk_filas_servicio FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS funcionarios (
  id_funcionario BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario BIGINT UNSIGNED NOT NULL UNIQUE,
  id_sucursal BIGINT UNSIGNED NOT NULL,
  cargo VARCHAR(120) NOT NULL,
  estado ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  CONSTRAINT fk_funcionarios_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
  CONSTRAINT fk_funcionarios_sucursal FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS turnos (
  id_turno BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario BIGINT UNSIGNED NOT NULL,
  id_fila BIGINT UNSIGNED NOT NULL,
  numero VARCHAR(24) UNIQUE,
  hora_ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado ENUM('Pendiente','En atencion','Finalizado','Cancelado') NOT NULL DEFAULT 'Pendiente',
  KEY idx_turnos_fila_estado (id_fila,estado,id_turno),
  KEY idx_turnos_usuario (id_usuario),
  CONSTRAINT fk_turnos_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
  CONSTRAINT fk_turnos_fila FOREIGN KEY (id_fila) REFERENCES filas(id_fila)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS atenciones (
  id_atencion BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_turno BIGINT UNSIGNED NOT NULL UNIQUE,
  id_funcionario BIGINT UNSIGNED NOT NULL,
  hora_inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  hora_fin DATETIME NULL,
  observacion TEXT,
  CONSTRAINT fk_atenciones_turno FOREIGN KEY (id_turno) REFERENCES turnos(id_turno),
  CONSTRAINT fk_atenciones_funcionario FOREIGN KEY (id_funcionario) REFERENCES funcionarios(id_funcionario)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notificaciones (
  id_notificacion BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  id_usuario BIGINT UNSIGNED NOT NULL,
  id_turno BIGINT UNSIGNED NOT NULL,
  mensaje TEXT NOT NULL,
  estado ENUM('pendiente','enviada','leida') NOT NULL DEFAULT 'pendiente',
  fecha_envio DATETIME NULL,
  KEY idx_notificaciones_turno (id_turno),
  CONSTRAINT fk_notificaciones_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
  CONSTRAINT fk_notificaciones_turno FOREIGN KEY (id_turno) REFERENCES turnos(id_turno)
) ENGINE=InnoDB;

-- Tabla auxiliar para la pantalla de configuración del prototipo; no es una entidad del MER.
CREATE TABLE IF NOT EXISTS configuracion (
  clave VARCHAR(50) PRIMARY KEY,
  valor VARCHAR(100) NOT NULL
) ENGINE=InnoDB;
INSERT IGNORE INTO configuracion (clave,valor) VALUES ('prioridad','llegada');

-- Datos de demostración. Modifica la sucursal antes de usar información real.
INSERT INTO sucursales (nombre,direccion,comuna,telefono)
SELECT 'Sucursal principal','Dirección por definir','Comuna por definir',NULL
WHERE NOT EXISTS (SELECT 1 FROM sucursales);

INSERT INTO servicios (id_sucursal,nombre,descripcion,duracion_estimada)
SELECT s.id_sucursal, x.nombre, x.descripcion, x.duracion
FROM sucursales s
JOIN (
 SELECT 'Atencion general' nombre,'Atención general' descripcion,10 duracion
 UNION ALL SELECT 'Servicio tecnico','Soporte técnico',15
 UNION ALL SELECT 'Consulta','Consultas',10
) x
WHERE s.nombre = 'Sucursal principal'
  AND NOT EXISTS (SELECT 1 FROM servicios v WHERE v.id_sucursal=s.id_sucursal AND v.nombre=x.nombre);

INSERT INTO filas (id_servicio,nombre)
SELECT id_servicio,'Fila principal' FROM servicios v
WHERE NOT EXISTS (SELECT 1 FROM filas f WHERE f.id_servicio=v.id_servicio AND f.nombre='Fila principal');
