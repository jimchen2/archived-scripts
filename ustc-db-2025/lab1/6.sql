DELIMITER //

-- Trigger A
CREATE TRIGGER after_reserve_insert 
AFTER INSERT ON Reserve -- 当一本书被预约时
FOR EACH ROW
BEGIN
    DECLARE book_borrowed INT;

    SELECT COUNT(*) INTO book_borrowed 
    FROM Borrow 
    WHERE book_ID = NEW.book_ID AND return_Date IS NULL;
    
    -- 如果没有被借出 则自动将 Book 表中相应图书的 bstatus 修改为 2
    IF book_borrowed = 0 THEN
        UPDATE Book 
        SET bstatus = 2 
        WHERE bid = NEW.book_ID;

        -- 并增加 reserve_Times
        UPDATE Book
        SET reserve_Times = reserve_Times + 1
        WHERE bid = NEW.book_ID;
    END IF;
END //






-- Trigger B & C
CREATE TRIGGER after_reserve_delete
AFTER DELETE ON Reserve -- 当某本预约的书被借出时或者读者取消预约时, 当某本预约的书被借出时或者读者取消预约时
FOR EACH ROW
BEGIN
    DECLARE remaining_reservations INT;
    DECLARE is_borrowed INT;
    
    -- 自动减少 reserve_Times
    UPDATE Book
    SET reserve_Times = reserve_Times - 1
    WHERE bid = OLD.book_ID;
    
    SELECT COUNT(*) INTO remaining_reservations
    FROM Reserve
    WHERE book_ID = OLD.book_ID;
    
    SELECT COUNT(*) INTO is_borrowed
    FROM Borrow
    WHERE book_ID = OLD.book_ID AND return_Date IS NULL;
    
    -- 当某本书的最后一位预约者取消预约时, 将bstatus改为 0
    IF remaining_reservations = 0 AND is_borrowed = 0 THEN
        UPDATE Book
        SET bstatus = 0
        WHERE bid = OLD.book_ID;
    END IF;
END //

DELIMITER ;


-- Initial state
SELECT bid, bstatus, reserve_Times FROM Book WHERE bid = 'B007';

-- D为‘R001’的读者预约ID为‘B007’的书
INSERT INTO Reserve (book_ID, reader_ID, reserve_Date, take_Date)
VALUES ('B007', 'R001', "2025-01-01", "2025-01-10");

SELECT bid, bstatus, reserve_Times FROM Book WHERE bid = 'B007';

-- 再取消预约的请求
DELETE FROM Reserve 
WHERE book_ID = 'B007' AND reader_ID = 'R001';

-- 展示过程中reserve_Times 和 bstatus 的变化
SELECT bid, bstatus, reserve_Times FROM Book WHERE bid = 'B007';
