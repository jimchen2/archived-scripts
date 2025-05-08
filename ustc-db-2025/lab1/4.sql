DELIMITER //

CREATE PROCEDURE borrowBook(
    IN p_reader_ID CHAR(8),
    IN p_book_ID CHAR(8),
    IN p_borrow_Date DATE,
    OUT p_message VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_current_borrows INT;
    DECLARE v_book_status INT;
    DECLARE v_has_reservation INT;
    DECLARE v_same_day_borrow INT;
    
    -- Start transaction
    START TRANSACTION;
    
    -- Requirement A
    SELECT COUNT(*) INTO v_same_day_borrow
    FROM Borrow
    WHERE reader_ID = p_reader_ID 
    AND book_ID = p_book_ID 
    AND borrow_Date = p_borrow_Date; 
    
    IF v_same_day_borrow > 0 THEN
        SET p_message = 'Error: Reader cannot borrow the same book twice in one day';
        ROLLBACK;
        SELECT p_message;
        LEAVE proc_label;
    END IF;
    
    -- Check if book exists and get status
    SELECT bstatus INTO v_book_status
    FROM Book
    WHERE bid = p_book_ID;
    
    IF v_book_status IS NULL THEN
        SET p_message = 'Error: Book does not exist';
        ROLLBACK;
        SELECT p_message;
        LEAVE proc_label;
    END IF;
    
    -- Requirement B
    SELECT COUNT(*) INTO v_has_reservation
    FROM Reserve
    WHERE book_ID = p_book_ID 
    AND reader_ID = p_reader_ID
    AND reserve_Date <= p_borrow_Date
    AND (take_Date >= p_borrow_Date OR take_Date IS NULL); -- Req B: Check reservation
    
    IF v_book_status = 2 AND v_has_reservation = 0 THEN
        SET p_message = 'Error: Book is reserved by another reader';
        ROLLBACK;
        SELECT p_message;
        LEAVE proc_label;
    END IF;

    IF v_book_status = 1 THEN
        SET p_message = 'Error: Book is borrowed';
        ROLLBACK;
        SELECT p_message;
        LEAVE proc_label;
    END IF;
    
    -- Requirement C
    SELECT COUNT(*) INTO v_current_borrows
    FROM Borrow
    WHERE reader_ID = p_reader_ID 
    AND return_Date IS NULL; 
    
    IF v_current_borrows >= 3 THEN
        SET p_message = 'Error: Reader has already borrowed maximum 3 books';
        ROLLBACK;
        SELECT p_message;
        LEAVE proc_label;
    END IF;
    
    -- Insert borrow record
    INSERT INTO Borrow (book_ID, reader_ID, borrow_Date, return_Date)
    VALUES (p_book_ID, p_reader_ID, p_borrow_Date, NULL);
    
    -- Requirement E
    UPDATE Book 
    SET borrow_Times = borrow_Times + 1
    WHERE bid = p_book_ID; 
    
    -- Requirement F
    UPDATE Book 
    SET bstatus = 1
    WHERE bid = p_book_ID;
    
    -- Requirement D
    DELETE FROM Reserve 
    WHERE book_ID = p_book_ID 
    AND reader_ID = p_reader_ID; 
    
    SET p_message = 'Book borrowed successfully';
    COMMIT;
    SELECT p_message;
    
END //

DELIMITER ;


-- Test cases
-- Test case 1
SET @message = '';
CALL borrowBook('R001', 'B008', '2024-04-03', @message);
SELECT @message;

-- Test case 2
SET @message = '';
CALL borrowBook('R001', 'B006', '2024-04-03', @message);
SELECT @message;

-- 并展示预约表相关预约记录被删除
SELECT * FROM Reserve WHERE book_ID = 'B006' AND reader_ID = 'R001';
-- 以及图书表对应书籍的times和status属性的变化
SELECT bid, borrow_Times, bstatus FROM Book WHERE bid = 'B006';

-- Test case 3
SET @message = '';
CALL borrowBook('R001', 'B006', '2024-04-03', @message);
SELECT @message;

-- Test case 4
SET @message = '';
CALL borrowBook('R001', 'B007', '2024-04-03', @message);
SELECT @message;