-- 2.1
SELECT b.bid, b.bname, br.borrow_Date
FROM Reader r
JOIN Borrow br ON r.rid = br.reader_ID
JOIN Book b ON br.book_ID = b.bid
WHERE r.rname = 'Rose';


-- 2.2
SELECT r.rid, r.rname
FROM Reader r
WHERE r.rid NOT IN (
    SELECT reader_ID FROM Borrow
    UNION
    SELECT reader_ID FROM Reserve
);


-- 2.3
SELECT b.author
FROM Borrow br
JOIN Book b ON br.book_ID = b.bid
GROUP BY b.author
ORDER BY COUNT(*) DESC
LIMIT 1;

-- 2.4

SELECT b.bid, b.bname
FROM Book b
JOIN Borrow br ON b.bid = br.book_ID
WHERE b.bname LIKE '%MySQL%'
AND br.return_Date IS NULL;

-- 2.5

SELECT r.rname
FROM Reader r
JOIN Borrow br ON r.rid = br.reader_ID
GROUP BY r.rid
HAVING COUNT(*) > 3;

-- 2.6


SELECT r.rid, r.rname
FROM Reader r
WHERE r.rid NOT IN (
    SELECT br.reader_ID
    FROM Borrow br
    JOIN Book b ON br.book_ID = b.bid
    WHERE b.author = 'J.K. Rowling'
);

-- 2.7


SELECT r.rid, r.rname, COUNT(*) as borrow_count
FROM Reader r
JOIN Borrow br ON r.rid = br.reader_ID
WHERE YEAR(br.borrow_Date) = 2024
GROUP BY r.rid, r.rname
ORDER BY borrow_count DESC
LIMIT 3;

-- 2.8


CREATE VIEW ReaderBorrowInfo AS
SELECT r.rid, r.rname, b.bid, b.bname, br.borrow_Date
FROM Reader r
JOIN Borrow br ON r.rid = br.reader_ID
JOIN Book b ON br.book_ID = b.bid;

SELECT rid, COUNT(DISTINCT bid) AS distinct_book_count
FROM ReaderBorrowInfo
WHERE YEAR(borrow_Date) = 2024
GROUP BY rid;