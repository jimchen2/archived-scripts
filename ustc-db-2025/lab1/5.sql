DELIMITER //

CREATE PROCEDURE returnBook(
    IN p_reader_ID CHAR(8),
    IN p_book_ID CHAR(8),
    IN p_return_Date DATE,
    OUT p_message VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_borrow_exists INT;
    DECLARE v_has_reservation INT;
    
    START TRANSACTION;
    
    -- Check if the borrow record exists
    SELECT COUNT(*) INTO v_borrow_exists
    FROM Borrow
    WHERE reader_ID = p_reader_ID 
    AND book_ID = p_book_ID 
    AND return_Date IS NULL;
    
    IF v_borrow_exists = 0 THEN
        SET p_message = 'Error: No active borrow record found for this reader and book';
        ROLLBACK;
        SELECT p_message;
        LEAVE proc_label;
    END IF;
    
    -- Requirement A: 还书后补上borrow表中对应记录的return_date
    UPDATE Borrow
    SET return_Date = p_return_Date
    WHERE reader_ID = p_reader_ID 
    AND book_ID = p_book_ID 
    AND return_Date IS NULL;
    

    -- Requirement B
    SELECT COUNT(*) INTO v_has_reservation
    FROM Reserve
    WHERE book_ID = p_book_ID;

    IF v_has_reservation > 0 THEN
        UPDATE Book
        SET bstatus = 2  -- Has reservations
        WHERE bid = p_book_ID;
    ELSE
        UPDATE Book
        SET bstatus = 0  -- No reservations
        WHERE bid = p_book_ID;
    END IF;
    
    SET p_message = 'Book returned successfully';
    COMMIT;
    SELECT p_message;
    
END //

DELIMITER ;


-- Test case 1
SET @message = '';
CALL returnBook('R001', 'B008', "2025-05-08", @message);
SELECT @message;

-- Test case 2
SET @message = '';
CALL returnBook('R001', 'B001', "2025-05-08", @message);
SELECT @message;

-- 展示相关书籍在book表中的status
SELECT bid, bstatus FROM Book WHERE bid = 'B001';
-- 在borrow表中的return_date的变化
SELECT book_ID, reader_ID, borrow_Date, return_Date FROM Borrow 
WHERE book_ID = 'B001' AND reader_ID = 'R001';