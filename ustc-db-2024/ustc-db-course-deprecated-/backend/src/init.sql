USE teacher_management;

CREATE TABLE teachers (
    id CHAR(5) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    gender INT CHECK (gender BETWEEN 1 AND 10),
    title INT CHECK (title BETWEEN 1 AND 11)
);

CREATE TABLE teacher_password (
    teacher_id CHAR(5) PRIMARY KEY,
    password_hash VARCHAR(256) NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

CREATE TABLE papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    source VARCHAR(256),
    year INT,
    type INT CHECK (type BETWEEN 1 AND 4),
    level INT CHECK (level BETWEEN 1 AND 6)
);

CREATE TABLE published_papers (
    paper_id INT,
    teacher_id CHAR(5),
    ranking INT CHECK (ranking >= 1),
    is_corresponding_author BOOLEAN,
    PRIMARY KEY (paper_id, teacher_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    UNIQUE (paper_id, ranking)
);

CREATE TABLE projects (
    id VARCHAR(256) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    source VARCHAR(256),
    project_type INT CHECK (project_type BETWEEN 1 AND 5),
    total_funding FLOAT,
    start_year INT,
    end_year INT
);

CREATE TABLE project_participants (
    project_id VARCHAR(256),
    teacher_id CHAR(5),
    ranking INT CHECK (ranking >= 1),
    funding FLOAT,
    PRIMARY KEY (project_id, teacher_id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
    UNIQUE (project_id, ranking)
);

CREATE TABLE courses (
    id VARCHAR(256) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    total_hours INT,
    level INT CHECK (level BETWEEN 1 AND 2)
);

CREATE TABLE taught_courses (
    course_id VARCHAR(256),
    teacher_id CHAR(5),
    year INT,
    term INT CHECK (term BETWEEN 1 AND 3),
    teaching_hours INT,
    PRIMARY KEY (course_id, teacher_id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);
