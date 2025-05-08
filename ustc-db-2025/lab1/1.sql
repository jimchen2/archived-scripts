CREATE DATABASE IF NOT EXISTS LibraryDB;
USE LibraryDB;


CREATE TABLE Reader (
    rid CHAR(8) PRIMARY KEY,
    rname VARCHAR(20),
    age INT,
    address VARCHAR(100)
);


CREATE TABLE Book (
    bid CHAR(8) PRIMARY KEY,
    bname VARCHAR(100) NOT NULL,
    author VARCHAR(50),
    price FLOAT,
    bstatus INT DEFAULT 0, -- 0:可借, 1:借出, 2:预约
    borrow_Times INT DEFAULT 0,
    reserve_Times INT DEFAULT 0
);


CREATE TABLE Borrow (
    book_ID CHAR(8),
    reader_ID CHAR(8),
    borrow_Date DATE,
    return_Date DATE,
    PRIMARY KEY (book_ID, reader_ID, borrow_Date),
    FOREIGN KEY (book_ID) REFERENCES Book(bid),
    FOREIGN KEY (reader_ID) REFERENCES Reader(rid)
);

CREATE TABLE Reserve (
    book_ID CHAR(8),
    reader_ID CHAR(8),
    reserve_Date DATE DEFAULT (CURRENT_DATE),
    take_Date DATE,
    PRIMARY KEY (book_ID, reader_ID, reserve_Date), -- Corrected from borrow_Date to reserve_Date
    FOREIGN KEY (book_ID) REFERENCES Book(bid),
    FOREIGN KEY (reader_ID) REFERENCES Reader(rid),
    CHECK (take_Date > reserve_Date)
);




-- 读者表
INSERT INTO Reader (rid, rname, age, address) VALUES
('R001', 'Rose', 25, '北京'),
('R002', 'John', 30, '上海'),
('R003', 'Lily', 22, '广州'),
('R004', 'Mike', 28, '深圳'),
('R005', 'Anna', 35, '杭州'),
('R006', 'Tom', 35, '杭州');
-- 图书表
INSERT INTO Book (bid, bname, author, price, bstatus, borrow_Times,
reserve_Times) VALUES
('B001', 'MySQL入门', '张三', 45.5, 1, 2, 0),
('B002', '深入MySQL', '李四', 56.0, 2, 1, 1),
('B003', '哈利波特1', 'J.K. Rowling', 60.0, 1, 3, 0),
('B004', '哈利波特2', 'J.K. Rowling', 65.0, 0, 0, 0),
('B005', '数据库原理', '王五', 70.0, 1, 2, 0),
('B006', '算法导论', '赵六', 80.0, 2, 0, 1),
('B007', 'Python编程', '张三', 55.0, 0, 2, 0),
('B009', 'java编程', '张三', 55.0, 1, 1, 0),
('B008', '算法基础', '赵九', 80.0, 2, 0, 1);
-- 借阅表
INSERT INTO Borrow (book_ID, reader_ID, borrow_Date, return_Date) VALUES
('B001', 'R001', '2024-03-01', NULL),
('B005', 'R001', '2023-12-15', '2024-01-10'),
('B003', 'R001', '2024-02-01', '2024-02-28'),
('B003', 'R002', '2024-04-01', NULL),
('B001', 'R004', '2024-01-05', '2024-01-20'),
('B002', 'R004', '2024-02-10', '2024-03-01'),
('B003', 'R004', '2024-03-15', '2024-03-16'),
('B005', 'R004', '2024-04-01', NULL),
('B007', 'R005', '2024-03-20', '2024-04-10'),
('B007', 'R005', '2024-03-10', '2024-03-15'),
('B009','R001','2024-03-01',NULL);
-- 预约表
INSERT INTO Reserve (book_ID, reader_ID, reserve_Date, take_Date) VALUES
('B006', 'R001', '2024-04-01', '2024-04-05'),
('B002', 'R002', '2024-04-02', '2024-04-06'),
('B008', 'R006', '2024-04-03', '2024-04-07');