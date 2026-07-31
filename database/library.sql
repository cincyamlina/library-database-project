PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS Loans;
DROP TABLE IF EXISTS Books;
DROP TABLE IF EXISTS Authors;
DROP TABLE IF EXISTS Members;

CREATE TABLE Members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    membership_date TEXT NOT NULL
);

CREATE TABLE Authors (
    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    UNIQUE(first_name, last_name)
);

CREATE TABLE Books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    isbn TEXT NOT NULL UNIQUE,
    publication_year INTEGER CHECK (
        publication_year IS NULL
        OR publication_year BETWEEN 1000 AND 2100
    ),
    total_copies INTEGER NOT NULL CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL CHECK (
        available_copies >= 0
        AND available_copies <= total_copies
    ),
    author_id INTEGER NOT NULL,
    FOREIGN KEY (author_id)
        REFERENCES Authors(author_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE Loans (
    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    checkout_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    FOREIGN KEY (member_id)
        REFERENCES Members(member_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (book_id)
        REFERENCES Books(book_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CHECK (date(due_date) > date(checkout_date)),
    CHECK (
        return_date IS NULL
        OR date(return_date) >= date(checkout_date)
    )
);

CREATE UNIQUE INDEX one_active_loan_per_member_book
ON Loans(member_id, book_id)
WHERE return_date IS NULL;

INSERT INTO Members
    (first_name, last_name, email, phone, membership_date)
VALUES
    ('Alexis', 'Amlin', 'alexis@example.com', '555-111-2222', '2026-01-15'),
    ('Jordan', 'Smith', 'jordan@example.com', '555-222-3333', '2026-02-10'),
    ('Taylor', 'Brown', 'taylor@example.com', '555-333-4444', '2026-03-05'),
    ('Morgan', 'Davis', 'morgan@example.com', '555-444-5555', '2026-04-20');

INSERT INTO Authors
    (first_name, last_name)
VALUES
    ('George', 'Orwell'),
    ('Jane', 'Austen'),
    ('Harper', 'Lee'),
    ('F. Scott', 'Fitzgerald'),
    ('Mary', 'Shelley'),
    ('Ray', 'Bradbury');

INSERT INTO Books
    (title, isbn, publication_year, total_copies, available_copies, author_id)
VALUES
    ('1984', '9780451524935', 1949, 4, 3, 1),
    ('Pride and Prejudice', '9780141439518', 1813, 3, 2, 2),
    ('To Kill a Mockingbird', '9780061120084', 1960, 5, 4, 3),
    ('The Great Gatsby', '9780743273565', 1925, 2, 2, 4),
    ('Frankenstein', '9780486282114', 1818, 3, 2, 5),
    ('Fahrenheit 451', '9781451673319', 1953, 2, 2, 6);

INSERT INTO Loans
    (member_id, book_id, checkout_date, due_date, return_date)
VALUES
    (1, 1, '2026-07-01', '2026-07-15', NULL),
    (2, 3, '2026-07-05', '2026-07-19', NULL),
    (1, 5, '2026-06-10', '2026-06-24', '2026-06-22'),
    (3, 2, '2026-06-15', '2026-06-29', NULL);

-- Query 1: Display all books with their authors.
SELECT
    Books.book_id,
    Books.title,
    Authors.first_name || ' ' || Authors.last_name AS author,
    Books.publication_year,
    Books.total_copies,
    Books.available_copies
FROM Books
JOIN Authors
    ON Books.author_id = Authors.author_id
ORDER BY Books.title;

-- Query 2: Display books that are currently available.
SELECT
    book_id,
    title,
    available_copies
FROM Books
WHERE available_copies > 0
ORDER BY title;

-- Query 3: Multi-table query showing members and books borrowed.
SELECT
    Members.first_name || ' ' || Members.last_name AS member,
    Books.title,
    Loans.checkout_date,
    Loans.due_date,
    Loans.return_date
FROM Loans
JOIN Members
    ON Loans.member_id = Members.member_id
JOIN Books
    ON Loans.book_id = Books.book_id
ORDER BY Members.last_name, Loans.checkout_date;

-- Query 4: Display active loans.
SELECT
    Loans.loan_id,
    Members.first_name || ' ' || Members.last_name AS member,
    Books.title,
    Loans.checkout_date,
    Loans.due_date
FROM Loans
JOIN Members
    ON Loans.member_id = Members.member_id
JOIN Books
    ON Loans.book_id = Books.book_id
WHERE Loans.return_date IS NULL
ORDER BY Loans.due_date;

-- Query 5: Count loans per member.
SELECT
    Members.member_id,
    Members.first_name || ' ' || Members.last_name AS member,
    COUNT(Loans.loan_id) AS number_of_loans
FROM Members
LEFT JOIN Loans
    ON Members.member_id = Loans.member_id
GROUP BY Members.member_id
ORDER BY number_of_loans DESC, member;
