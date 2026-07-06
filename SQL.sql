
USE bdms;
DELIMITER $$

DROP TRIGGER IF EXISTS trg_donor_check $$
CREATE TRIGGER trg_donor_check
BEFORE INSERT ON donor
FOR EACH ROW
BEGIN
    IF TIMESTAMPDIFF(YEAR, NEW.dob, CURDATE()) < 18 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Donor must be at least 18 years old.';
    END IF;
    IF EXISTS (SELECT 1 FROM recipient WHERE cnic = NEW.cnic) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This person is already a recipient; a donor cannot be their own recipient.';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_recipient_check $$
CREATE TRIGGER trg_recipient_check
BEFORE INSERT ON recipient
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM donor WHERE cnic = NEW.cnic) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'This person is already a donor; a donor cannot be their own recipient.';
    END IF;
END $$

DROP TRIGGER IF EXISTS trg_donation_gap $$
CREATE TRIGGER trg_donation_gap
BEFORE INSERT ON donation_history
FOR EACH ROW
BEGIN
    DECLARE last_date DATE;
    SELECT MAX(donation_date) INTO last_date FROM donation_history WHERE donor_id = NEW.donor_id;
    IF last_date IS NOT NULL AND NEW.donation_date < DATE_ADD(last_date, INTERVAL 2 MONTH) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Donor must wait at least 2 months between donations.';
    END IF;
END $$

DELIMITER ;
