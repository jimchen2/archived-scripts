
DELIMITER //

CREATE PROCEDURE updateReaderID(IN old_id CHAR(8), IN new_id CHAR(8))
BEGIN
    DECLARE exit_handler INT DEFAULT 0;
    START TRANSACTION;
    
    -- Check if old_id exists
    IF NOT EXISTS (SELECT * FROM Reader WHERE rid = old_id) THEN
        SET exit_handler = 1;
        SELECT 'Error: The original reader ID does not exist.' AS Message;
    END IF;
    
    -- Check if new_id already exists
    IF EXISTS (SELECT * FROM Reader WHERE rid = new_id) THEN
        SET exit_handler = 1;
        SELECT 'Error: The new reader ID already exists.' AS Message;
    END IF;
    
    IF exit_handler = 0 THEN
        -- Create a temporary duplicate entry
        INSERT INTO Reader (rid, rname, age, address)
        SELECT new_id, rname, age, address FROM Reader WHERE rid = old_id;
        
        UPDATE Borrow SET reader_ID = new_id 
        WHERE reader_ID = old_id;
        
        UPDATE Reserve SET reader_ID = new_id 
        WHERE reader_ID = old_id;
        DELETE FROM Reader WHERE rid = old_id;
        COMMIT;
    ELSE
        ROLLBACK;
    END IF;
END //

DELIMITER ;


-- Call
CALL updateReaderID('R006', 'R999');


SELECT * FROM Reader WHERE rid = 'R999';
SELECT * FROM Reader WHERE rid = 'R006';
SELECT * FROM Borrow WHERE reader_ID = 'R999';
SELECT * FROM Reserve WHERE reader_ID = 'R999';
