CREATE DATABASE IF NOT EXISTS bancos_mexico;
USE bancos_mexico;

-- 1. Tipos de Institución
CREATE TABLE IF NOT EXISTS tipos_institucion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Instituciones Financieras (Bancos)
CREATE TABLE IF NOT EXISTS instituciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    tipo_id INT NOT NULL,
    FOREIGN KEY (tipo_id) REFERENCES tipos_institucion(id) ON DELETE CASCADE
);

-- 3. Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    edad INT NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

-- 4. Tokens de Recuperación
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    fecha_expiracion DATETIME NOT NULL,
    usado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- 5. Créditos (Mejora de deudas)
CREATE TABLE IF NOT EXISTS creditos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    institucion_id INT NOT NULL,
    limite_credito DECIMAL(15, 2) NOT NULL,
    deuda_actual DECIMAL(15, 2) NOT NULL,
    tasa_anual DECIMAL(5, 2) NOT NULL,
    pago_minimo DECIMAL(15, 2) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (institucion_id) REFERENCES instituciones(id) ON DELETE CASCADE
);

-- 6. Categorías de Gasto
CREATE TABLE IF NOT EXISTS categorias_gasto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE -- (Hormiga, Fijo, Variable)
);

-- 7. Gastos (Detector de fugas)
CREATE TABLE IF NOT EXISTS gastos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    categoria_id INT NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    monto DECIMAL(15, 2) NOT NULL,
    fecha DATE NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias_gasto(id) ON DELETE CASCADE
);

-- Insertar Datos Iniciales Básicos
INSERT IGNORE INTO tipos_institucion (nombre) VALUES ('Banco Múltiple'), ('Sociedad Financiera Popular (SOFIPO)'), ('Fintech');
INSERT IGNORE INTO instituciones (nombre, tipo_id) VALUES ('BBVA Bancomer', 1), ('Banamex', 1), ('Nu México', 3), ('Klar', 3);
INSERT IGNORE INTO categorias_gasto (nombre) VALUES ('Hormiga'), ('Fijo'), ('Variable');
