CREATE DATABASE IF NOT EXISTS vehicle_service_center
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE vehicle_service_center;

-- 1. Administrator accounts
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT NOT NULL AUTO_INCREMENT,
    admin_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    PRIMARY KEY (admin_id),
    UNIQUE KEY uq_admin_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Customer accounts and email verification
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT NOT NULL AUTO_INCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100) DEFAULT NULL,
    address VARCHAR(255) DEFAULT NULL,
    password_hash VARCHAR(255) DEFAULT NULL,
    email_verified TINYINT(1) NOT NULL DEFAULT 0,
    verification_token_hash CHAR(64) DEFAULT NULL,
    verification_expires_at DATETIME DEFAULT NULL,
    PRIMARY KEY (customer_id),
    UNIQUE KEY uq_customer_phone (phone),
    UNIQUE KEY uq_customer_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Services
CREATE TABLE IF NOT EXISTS services (
    service_id INT NOT NULL AUTO_INCREMENT,
    service_name VARCHAR(100) NOT NULL,
    description VARCHAR(255) DEFAULT NULL,
    vehicle_type VARCHAR(20) NOT NULL DEFAULT 'Car',
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (service_id),
    UNIQUE KEY uq_service_name (service_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Technicians
CREATE TABLE IF NOT EXISTS technicians (
    technician_id INT NOT NULL AUTO_INCREMENT,
    technician_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    specialization VARCHAR(100) DEFAULT NULL,
    vehicle_type VARCHAR(20) NOT NULL DEFAULT 'All',
    experience INT DEFAULT NULL,
    PRIMARY KEY (technician_id),
    UNIQUE KEY uq_technician_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Customer vehicles
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INT NOT NULL AUTO_INCREMENT,
    customer_id INT NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL DEFAULT 'Car',
    vehicle_number VARCHAR(20) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    manufacture_year INT DEFAULT NULL,
    PRIMARY KEY (vehicle_id),
    UNIQUE KEY uq_vehicle_number (vehicle_number),
    KEY idx_vehicles_customer (customer_id),
    CONSTRAINT fk_vehicles_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Spare-parts inventory
CREATE TABLE IF NOT EXISTS parts (
    part_id INT NOT NULL AUTO_INCREMENT,
    part_name VARCHAR(100) NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL DEFAULT 'All',
    part_number VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (part_id),
    UNIQUE KEY uq_part_name (part_name),
    UNIQUE KEY uq_part_number (part_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Appointments
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT NOT NULL AUTO_INCREMENT,
    customer_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    service_id INT NOT NULL,
    technician_id INT DEFAULT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    PRIMARY KEY (appointment_id),
    KEY idx_appointments_customer (customer_id),
    KEY idx_appointments_vehicle (vehicle_id),
    KEY idx_appointments_service (service_id),
    KEY idx_appointments_technician (technician_id),
    CONSTRAINT fk_appointments_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    CONSTRAINT fk_appointments_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id),
    CONSTRAINT fk_appointments_service
        FOREIGN KEY (service_id)
        REFERENCES services(service_id),
    CONSTRAINT fk_appointments_technician
        FOREIGN KEY (technician_id)
        REFERENCES technicians(technician_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Service estimates
CREATE TABLE IF NOT EXISTS estimates (
    estimate_id INT NOT NULL AUTO_INCREMENT,
    appointment_id INT NOT NULL,
    estimate_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    service_name VARCHAR(100) NOT NULL,
    service_amount DECIMAL(10,2) NOT NULL,
    parts_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    notes TEXT,
    PRIMARY KEY (estimate_id),
    KEY idx_estimates_appointment (appointment_id),
    CONSTRAINT fk_estimates_appointment
        FOREIGN KEY (appointment_id)
        REFERENCES appointments(appointment_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Parts included in estimates
CREATE TABLE IF NOT EXISTS estimate_parts (
    estimate_part_id INT NOT NULL AUTO_INCREMENT,
    estimate_id INT NOT NULL,
    part_id INT NOT NULL,
    part_name VARCHAR(100) NOT NULL,
    part_number VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (estimate_part_id),
    KEY idx_estimate_parts_estimate (estimate_id),
    KEY idx_estimate_parts_part (part_id),
    CONSTRAINT fk_estimate_parts_estimate
        FOREIGN KEY (estimate_id)
        REFERENCES estimates(estimate_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_estimate_parts_part
        FOREIGN KEY (part_id)
        REFERENCES parts(part_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Final invoices
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INT NOT NULL AUTO_INCREMENT,
    appointment_id INT NOT NULL,
    invoice_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    service_name VARCHAR(100) NOT NULL,
    service_amount DECIMAL(10,2) NOT NULL,
    parts_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    payment_method VARCHAR(30) DEFAULT NULL,
    notes TEXT,
    PRIMARY KEY (invoice_id),
    UNIQUE KEY uq_invoice_appointment (appointment_id),
    CONSTRAINT fk_invoices_appointment
        FOREIGN KEY (appointment_id)
        REFERENCES appointments(appointment_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Parts included in invoices
CREATE TABLE IF NOT EXISTS invoice_parts (
    invoice_part_id INT NOT NULL AUTO_INCREMENT,
    invoice_id INT NOT NULL,
    part_id INT NOT NULL,
    part_name VARCHAR(100) NOT NULL,
    part_number VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (invoice_part_id),
    KEY idx_invoice_parts_invoice (invoice_id),
    KEY idx_invoice_parts_part (part_id),
    CONSTRAINT fk_invoice_parts_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_invoice_parts_part
        FOREIGN KEY (part_id)
        REFERENCES parts(part_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Password reset tokens
-- account_id identifies an admin or customer according to account_type.
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    reset_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    account_type VARCHAR(10) NOT NULL,
    account_id INT NOT NULL,
    token_hash CHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (reset_id),
    UNIQUE KEY uq_password_reset_token (token_hash),
    KEY idx_password_reset_account (account_type, account_id),
    KEY idx_password_reset_expiry (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SHOW TABLES;
