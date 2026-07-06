-- ============================================================
-- BLOOD DONATION MANAGEMENT SYSTEM (BDMS) - Sargodha, Pakistan
-- MySQL (XAMPP) + Python (Flask) + HTML
-- THREE ROLES: Admin, Donor, Recipient
-- ============================================================

DROP DATABASE IF EXISTS bdms;
CREATE DATABASE bdms CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE bdms;

CREATE TABLE blood_bank (
    bank_id   INT AUTO_INCREMENT PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL,
    address   VARCHAR(150) NOT NULL,
    city      VARCHAR(50)  NOT NULL DEFAULT 'Sargodha',
    contact   VARCHAR(20)  NOT NULL
);

CREATE TABLE hospital (
    hospital_id   INT AUTO_INCREMENT PRIMARY KEY,
    hospital_name VARCHAR(100) NOT NULL,
    address       VARCHAR(150) NOT NULL,
    city          VARCHAR(50)  NOT NULL DEFAULT 'Sargodha',
    contact       VARCHAR(20)  NOT NULL
);

-- DONOR entity
CREATE TABLE donor (
    donor_id           INT AUTO_INCREMENT PRIMARY KEY,
    full_name          VARCHAR(100) NOT NULL,
    cnic               VARCHAR(15)  NOT NULL UNIQUE,
    gender             ENUM('Male','Female') NOT NULL,
    dob                DATE NOT NULL,
    blood_group        ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    phone              VARCHAR(15)  NOT NULL,
    email              VARCHAR(100),
    address            VARCHAR(150) NOT NULL,
    city               VARCHAR(50)  NOT NULL DEFAULT 'Sargodha',
    last_donation_date DATE,
    registered_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RECIPIENT entity (separate from donor, as in the ER diagram)
CREATE TABLE recipient (
    recipient_id  INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    cnic          VARCHAR(15)  NOT NULL UNIQUE,
    gender        ENUM('Male','Female') NOT NULL,
    dob           DATE NOT NULL,
    blood_group   ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    phone         VARCHAR(15)  NOT NULL,
    email         VARCHAR(100),
    address       VARCHAR(150) NOT NULL,
    city          VARCHAR(50)  NOT NULL DEFAULT 'Sargodha',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- USERS login accounts (Chapter 11 security). role = admin / donor / recipient
-- A donor login links to a donor row; a recipient login links to a recipient row.
CREATE TABLE users (
    user_id      INT AUTO_INCREMENT PRIMARY KEY,
    username     VARCHAR(50)  NOT NULL UNIQUE,
    password     VARCHAR(255) NOT NULL,
    role         ENUM('admin','donor','recipient') NOT NULL DEFAULT 'donor',
    donor_id     INT,
    recipient_id INT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id)     REFERENCES donor(donor_id)         ON DELETE SET NULL,
    FOREIGN KEY (recipient_id) REFERENCES recipient(recipient_id) ON DELETE SET NULL
);

CREATE TABLE blood_unit (
    unit_id        INT AUTO_INCREMENT PRIMARY KEY,
    blood_group    ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    bank_id        INT NOT NULL,
    donor_id       INT,
    status         ENUM('available','reserved','used') NOT NULL DEFAULT 'available',
    collected_date DATE NOT NULL,
    FOREIGN KEY (bank_id)  REFERENCES blood_bank(bank_id),
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id) ON DELETE SET NULL
);

CREATE TABLE appointment (
    appointment_id   INT AUTO_INCREMENT PRIMARY KEY,
    donor_id         INT NOT NULL,
    bank_id          INT NOT NULL,
    appointment_date DATE NOT NULL,
    status           ENUM('scheduled','completed','cancelled') NOT NULL DEFAULT 'scheduled',
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (bank_id)  REFERENCES blood_bank(bank_id)
);

-- BLOOD REQUEST now links to a RECIPIENT (and a hospital)
CREATE TABLE blood_request (
    request_id     INT AUTO_INCREMENT PRIMARY KEY,
    recipient_id   INT,
    hospital_id    INT NOT NULL,
    patient_name   VARCHAR(100) NOT NULL,
    blood_group    ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    units_required INT NOT NULL DEFAULT 1,
    status         ENUM('pending','approved','rejected','fulfilled') NOT NULL DEFAULT 'pending',
    request_date   DATE NOT NULL,
    FOREIGN KEY (recipient_id) REFERENCES recipient(recipient_id) ON DELETE SET NULL,
    FOREIGN KEY (hospital_id)  REFERENCES hospital(hospital_id)
);

CREATE TABLE donation_history (
    donation_id   INT AUTO_INCREMENT PRIMARY KEY,
    donor_id      INT NOT NULL,
    bank_id       INT NOT NULL,
    donation_date DATE NOT NULL,
    blood_group   ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    units         INT NOT NULL DEFAULT 1,
    FOREIGN KEY (donor_id) REFERENCES donor(donor_id) ON DELETE CASCADE,
    FOREIGN KEY (bank_id)  REFERENCES blood_bank(bank_id)
);

-- Indexes (Chapter 5 - physical design)
CREATE INDEX idx_unit_group      ON blood_unit(blood_group);
CREATE INDEX idx_unit_status     ON blood_unit(status);
CREATE INDEX idx_donor_group     ON donor(blood_group);
CREATE INDEX idx_recipient_group ON recipient(blood_group);
CREATE INDEX idx_request_status  ON blood_request(status);

-- ===================== SAMPLE DATA (Sargodha) =====================

INSERT INTO blood_bank (bank_name, address, city, contact) VALUES
('DHQ Hospital Blood Bank',         'Civil Lines, Sargodha',     'Sargodha', '048-9230301'),
('Sargodha Red Crescent Blood Bank','Club Road, Sargodha',       'Sargodha', '048-3768900'),
('Niazi Welfare Blood Bank',        'University Road, Sargodha', 'Sargodha', '048-3220011');

INSERT INTO hospital (hospital_name, address, city, contact) VALUES
('DHQ Teaching Hospital Sargodha',  'Civil Lines, Sargodha',     'Sargodha', '048-9230300'),
('Niazi Medical & Dental Hospital', 'Faisalabad Road, Sargodha', 'Sargodha', '048-3768111'),
('Ittefaq Hospital Sargodha',       'Khushab Road, Sargodha',    'Sargodha', '048-3740555'),
('Mansoora Hospital',               'Satellite Town, Sargodha',  'Sargodha', '048-3211234');

INSERT INTO donor (full_name, cnic, gender, dob, blood_group, phone, email, address, city, last_donation_date) VALUES
('Muhammad Ahmed', '38401-1234567-1', 'Male',   '1995-03-12', 'O+',  '0300-1234567', 'ahmed@gmail.com',   'Satellite Town, Sargodha', 'Sargodha', '2026-02-10'),
('Fatima Bibi',    '38401-2345678-2', 'Female', '1998-07-25', 'B+',  '0321-2345678', 'fatima@gmail.com',  'University Road, Sargodha','Sargodha', '2026-01-15'),
('Bilal Hassan',   '38401-3456789-3', 'Male',   '1992-11-05', 'A+',  '0333-3456789', 'bilal@gmail.com',   'Khushab Road, Sargodha',   'Sargodha', '2026-03-01'),
('Ayesha Khan',    '38401-4567890-4', 'Female', '2000-01-30', 'AB+', '0345-4567890', 'ayesha@gmail.com',  'Civil Lines, Sargodha',    'Sargodha', NULL),
('Usman Ali',      '38401-5678901-5', 'Male',   '1990-06-18', 'O-',  '0301-5678901', 'usman@gmail.com',   'Club Road, Sargodha',      'Sargodha', '2025-12-20'),
('Zainab Tariq',   '38401-6789012-6', 'Female', '1997-09-09', 'A-',  '0322-6789012', 'zainab@gmail.com',  'Jail Road, Sargodha',      'Sargodha', NULL),
('Hamza Sheikh',   '38401-7890123-7', 'Male',   '1994-04-22', 'B-',  '0334-7890123', 'hamza@gmail.com',   'Block 7, Sargodha',        'Sargodha', '2026-02-28'),
('Mehwish Akram',  '38401-8901234-8', 'Female', '1999-12-14', 'O+',  '0346-8901234', 'mehwish@gmail.com', 'Faisalabad Road, Sargodha','Sargodha', NULL);

INSERT INTO recipient (full_name, cnic, gender, dob, blood_group, phone, email, address, city) VALUES
('Imran Yousaf',   '38401-1112223-1', 'Male',   '1988-05-10', 'O+', '0300-1112223', 'imran@gmail.com',  'Satellite Town, Sargodha', 'Sargodha'),
('Saima Riaz',     '38401-2223334-2', 'Female', '1993-08-19', 'A+', '0321-2223334', 'saima@gmail.com',  'Civil Lines, Sargodha',    'Sargodha'),
('Kashif Mehmood', '38401-3334445-3', 'Male',   '1985-02-27', 'B+', '0333-3334445', 'kashif@gmail.com', 'Khushab Road, Sargodha',   'Sargodha'),
('Nadia Aslam',    '38401-4445556-4', 'Female', '1996-11-03', 'AB+','0345-4445556', 'nadia@gmail.com',  'University Road, Sargodha','Sargodha');

-- Login accounts (passwords HASHED with pbkdf2:sha256)
--   admin  / admin123    (admin)
--   ahmed  / ahmed123    (donor)      -> donor 1
--   fatima / fatima123   (donor)      -> donor 2
--   imran  / imran123    (recipient)  -> recipient 1
--   saima  / saima123    (recipient)  -> recipient 2
INSERT INTO users (username, password, role, donor_id, recipient_id) VALUES
('admin',  'pbkdf2:sha256:1000000$8g5VJqxXxgXHMYkm$005f0a9bbbeb532c019687ce9f3a3074f682c29cbe101d69a54ce36815f1e7d6', 'admin',     NULL, NULL),
('ahmed',  'pbkdf2:sha256:1000000$ojWBt1R56umJIrM6$29710009bfbfc5736b26f9e43421c0f56cb1e3b6c72b3906ef79aff7efbd817f', 'donor',     1,    NULL),
('fatima', 'pbkdf2:sha256:1000000$jBp4bCFAsO83kWp7$682bd7a1afbfb946184a5fe1f933cd647a16fe393a26562a8b2e3eff2582411e', 'donor',     2,    NULL),
('imran',  'pbkdf2:sha256:1000000$AcraNCwmMR0clFdW$3f5e29f81af33527a3412336bd940869ca3940af0232e655a0849af2f039ca19', 'recipient', NULL, 1),
('saima',  'pbkdf2:sha256:1000000$3YKfFJHeLzAa8eFN$67a873492de9194f2e338ef178d7abfb74c7f0d076ae79e9eae40f370c761f56', 'recipient', NULL, 2);

INSERT INTO blood_unit (blood_group, bank_id, donor_id, status, collected_date) VALUES
('O+',  1, 1, 'available', '2026-02-10'),
('O+',  1, 8, 'available', '2026-06-01'),
('B+',  2, 2, 'available', '2026-01-15'),
('A+',  1, 3, 'available', '2026-03-01'),
('A+',  2, NULL, 'available', '2026-05-20'),
('O-',  3, 5, 'used',      '2025-12-20'),
('B-',  1, 7, 'available', '2026-02-28'),
('AB+', 2, NULL, 'available', '2026-04-11'),
('O+',  3, NULL, 'reserved',  '2026-05-30');

INSERT INTO appointment (donor_id, bank_id, appointment_date, status) VALUES
(4, 1, '2026-06-25', 'scheduled'),
(6, 2, '2026-06-28', 'scheduled'),
(1, 1, '2026-02-10', 'completed');

INSERT INTO blood_request (recipient_id, hospital_id, patient_name, blood_group, units_required, status, request_date) VALUES
(1, 1, 'Imran Yousaf',   'O+', 2, 'pending',   '2026-06-18'),
(2, 2, 'Saima Riaz',     'A+', 1, 'approved',  '2026-06-17'),
(3, 3, 'Kashif Mehmood', 'B+', 1, 'fulfilled', '2026-06-10');

INSERT INTO donation_history (donor_id, bank_id, donation_date, blood_group, units) VALUES
(1, 1, '2026-02-10', 'O+', 1),
(2, 2, '2026-01-15', 'B+', 1),
(3, 1, '2026-03-01', 'A+', 1),
(5, 3, '2025-12-20', 'O-', 1),
(7, 1, '2026-02-28', 'B-', 1);

-- ============================================================
-- VALIDATION TRIGGERS (added after evaluation feedback)
--   1. A donor must be at least 18 years old.
--   2. A donor must wait 2 months between donations.
--   3. A donor cannot be their own recipient (same CNIC).
-- ============================================================
DELIMITER $$

DROP TRIGGER IF EXISTS trg_donor_check $$
CREATE TRIGGER trg_donor_check
BEFORE INSERT ON donor
FOR EACH ROW
BEGIN
    -- Rule 1: at least 18 years old
    IF TIMESTAMPDIFF(YEAR, NEW.dob, CURDATE()) < 18 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Donor must be at least 18 years old.';
    END IF;
    -- Rule 3: must not already be a recipient
    IF EXISTS (SELECT 1 FROM recipient WHERE cnic = NEW.cnic) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'This person is already a recipient; a donor cannot be their own recipient.';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_recipient_check $$
CREATE TRIGGER trg_recipient_check
BEFORE INSERT ON recipient
FOR EACH ROW
BEGIN
    -- Rule 3: must not already be a donor
    IF EXISTS (SELECT 1 FROM donor WHERE cnic = NEW.cnic) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'This person is already a donor; a donor cannot be their own recipient.';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_donation_gap $$
CREATE TRIGGER trg_donation_gap
BEFORE INSERT ON donation_history
FOR EACH ROW
BEGIN
    DECLARE last_date DATE;
    -- Rule 2: at least 2 months since the donor's previous donation
    SELECT MAX(donation_date) INTO last_date
    FROM donation_history WHERE donor_id = NEW.donor_id;
    IF last_date IS NOT NULL AND NEW.donation_date < DATE_ADD(last_date, INTERVAL 2 MONTH) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Donor must wait at least 2 months between donations.';
    END IF;
END $$

DELIMITER ;
